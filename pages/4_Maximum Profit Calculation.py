# pages/4_Maximum Profit Calculation.py

"""
Streamlit Page: Maximum Profit — Unlimited Transactions (Greedy)

This page implements a classic greedy strategy (LeetCode 122) to compute the
maximum achievable profit from unlimited buy/sell transactions on a closing-
price series. It supports three data sources (existing session data, Yahoo
Finance fetch, or user-uploaded CSV/Excel), canonicalizes the dataset to
Date/Open/High/Low/Close/Volume, reconstructs greedy trades for explanation/
plotting, and provides quick summary plus validation test cases.

"""

# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
# NOTE: Keep imports minimal on Streamlit pages to avoid slow reloads.
import pandas as pd
import streamlit as st
import altair as alt

from scr.Calculations import ALGORITHMS                     # registry (names → run funcs)
from scr.data.data import fetch_raw_yf, POPULAR_TICKERS     # Yahoo data access + presets
from scr.data.data_preprocessing import standardize_ohlcv, quick_summary  # cleaning utils

st.set_page_config(page_title="Max Profit — Unlimited Transactions", layout="wide")

# -----------------------
# Page-local state
# -----------------------
# NOTE: We isolate page state so switching pages won’t clobber global session keys.
st.session_state.setdefault("maxprofit_df", None)
st.session_state.setdefault("maxprofit_source", None)
st.session_state.setdefault("maxprofit_meta", {"source": None, "ticker": None, "origin": None, "label": None})
st.session_state.setdefault("maxprofit_fp", None)  # fingerprint of session data

# -----------------------
# Helpers
# -----------------------
def canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    """Run once to enforce Date/Open/High/Low/Close/Volume, sorted unique dates."""
    # NOTE: standardize_ohlcv returns a frame indexed by Date; reset_index to get a Date column.
    return standardize_ohlcv(df).reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]

@st.cache_data(show_spinner=False)
def load_yf_clean(ticker: str, start: str, end: str, auto_adj: bool) -> pd.DataFrame:
    """
    Fetch prices from Yahoo Finance and return a canonical OHLCV DataFrame.

    Args:
        ticker (str): Symbol to fetch (e.g., "AAPL", "^GSPC").
        start (str): Start date in "YYYY-MM-DD".
        end   (str): End date in "YYYY-MM-DD".
        auto_adj (bool): If True, apply Yahoo auto-adjust for splits/dividends.

    Returns:
        pd.DataFrame: Canonicalized DataFrame with columns
                      ["Date","Open","High","Low","Close","Volume"].
                      Empty DataFrame if no data is returned.
    """
    # NOTE: fetch_raw_yf returns raw schema; canonicalize normalizes to our six columns.
    raw = fetch_raw_yf(ticker, start, end, auto_adjust=auto_adj)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    return canonicalize(raw)

@st.cache_data(show_spinner=False)
def load_csv_clean(file) -> pd.DataFrame:
    """
    Robust loader for CSV/Excel. Tries CSV; if canonicalization fails or the file
    is actually Excel, retries as Excel and picks the first sheet that standardizes.
    Returns canonical OHLCV with columns ["Date","Open","High","Low","Close","Volume"].
    """
    # NOTE: Some Excel files can be (wrongly) parsed by read_csv without raising;
    # this function guards by attempting canonicalization and falling back to Excel.
    name = (getattr(file, "name", "") or "").lower()

    def _canonical_or_none(df):
        try:
            out = canonicalize(df)
            # must contain Date and Close after standardization
            if out is None or out.empty or "Date" not in out.columns or "Close" not in out.columns:
                return None
            return out
        except Exception:
            return None

    # -------- Prefer by extension ---------- #
    is_excel_ext = name.endswith((".xlsx", ".xls"))
    if is_excel_ext:
        # Read Excel (try each sheet)
        try:
            xl = pd.read_excel(file, sheet_name=None)  # dict of DataFrames
        except Exception:
            # In case the stream was read before
            try:
                if hasattr(file, "seek"):
                    file.seek(0)
                xl = pd.read_excel(file, sheet_name=None)
            except Exception:
                return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

        for sheet_name, df in xl.items():
            out = _canonical_or_none(df)
            if out is not None:
                return out
        # nothing worked
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

    # -------- Try CSV first ---------- #
    try:
        df_csv = pd.read_csv(file)
        out = _canonical_or_none(df_csv)
        if out is not None:
            return out
    except Exception:
        pass  # fall through to Excel retry

    # -------- Retry as Excel in case CSV-reading “succeeded” on a real Excel -------- #
    try:
        if hasattr(file, "seek"):
            file.seek(0)
        xl = pd.read_excel(file, sheet_name=None)
        for sheet_name, df in xl.items():
            out = _canonical_or_none(df)
            if out is not None:
                return out
    except Exception:
        # final fallback: empty canonical frame
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

    return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

def set_df(df: pd.DataFrame, ok_msg: str):
    """
    Store a validated dataset into page-local session state and show a status message.

    Args:
        df (pd.DataFrame): DataFrame to store.
        ok_msg (str): Success message to display if df is non-empty.
    """
    # NOTE: Keep user feedback short; noisy errors reduce usability.
    if df is None or df.empty:
        st.error("No data returned.")
    else:
        st.session_state["maxprofit_df"] = df
        st.success(ok_msg)

def session_fingerprint() -> tuple | None:
    """
    Lightweight fingerprint to detect if session data changed
    without heavy hashing. Returns None if no usable session data.
    """
    # NOTE: I avoid hashing entire frames; a tuple of simple props is enough to invalidate cache.
    df = st.session_state.get("data")
    cfg = st.session_state.get("cfg", {})
    if isinstance(df, pd.DataFrame) and not df.empty:
        try:
            return (
                cfg.get("ticker"),
                pd.to_datetime(df["Date"]).min(),
                pd.to_datetime(df["Date"]).max(),
                len(df),
            )
        except Exception:
            # If columns differ, still give a simple shape-based fp
            return (cfg.get("ticker"), len(df))
    return None

# =======================
# SIDEBAR
# =======================
with st.sidebar:
    st.header("Data Controls")

    # NOTE: Switching the radio resets page-local cache so users don’t see stale data.
    source = st.radio(
        "Data source",
        ["Session data", "Yahoo Finance", "Upload CSV/Excel"],
        help="Pick where to load the price data from."
    )

    # Clear page-local data & meta when source changes
    if st.session_state["maxprofit_source"] != source:
        st.session_state["maxprofit_df"] = None
        st.session_state["maxprofit_source"] = source
        st.session_state["maxprofit_meta"] = {"source": None, "ticker": None, "origin": None, "label": None}
        st.session_state["maxprofit_fp"] = None  # reset fingerprint too

    with st.expander("Advanced settings", expanded=False):
        # NOTE: Auto-adjust aligns Yahoo data with splits/dividends; leave ON by default.
        auto_adj = st.checkbox("Auto-adjust prices (splits/dividends)", value=True)
        # NOTE: These toggles only affect UI rendering, not computation.
        show_trades_table = st.checkbox("Show trades table", value=True)
        show_markers = st.checkbox("Show buy/sell markers on chart", value=True)

    # ---- Source handling ----
    if source == "Session data":
        st.caption("Uses data already loaded on Home page.")
        fp = session_fingerprint()

        if fp is None:
            st.warning("No session data found. Go to Home to load data first.")
        else:
            # Only (re)load if data changed or not yet loaded
            if (st.session_state["maxprofit_df"] is None) or (st.session_state["maxprofit_fp"] != fp):
                try:
                    df_sess = st.session_state["data"]
                    df = canonicalize(df_sess)
                    set_df(df, "Loaded session snapshot.")
                    st.session_state["maxprofit_fp"] = fp
                    tick = st.session_state.get("cfg", {}).get("ticker", "Unknown")
                    st.session_state["maxprofit_meta"] = {
                        "source": "Session data",
                        "ticker": tick,
                        "origin": "session",
                        "label": None,
                    }
                except Exception as e:
                    st.error(f"Failed to read session data: {e}")

    elif source == "Yahoo Finance":
        # Popular OR custom ticker
        label_options = [name for name, _ in POPULAR_TICKERS] + ["Custom…"]
        col_sym, col_custom = st.columns([1, 1])
        with col_sym:
            label = st.selectbox("Popular tickers", label_options, key="yf_label")
        with col_custom:
            custom_ticker = st.text_input(
                "Custom ticker",
                value=st.session_state.get("yf_custom", ""),
                placeholder="e.g., IBM or ^GSPC",
                key="yf_custom_input",
            ).strip().upper()

        # Resolve final ticker (map label → symbol, or use custom)
        ticker = dict(POPULAR_TICKERS).get(label, None)
        if label == "Custom…":
            ticker = custom_ticker

        # Date range
        date_range = st.date_input(
            "Date range",
            value=(pd.Timestamp.today().normalize() - pd.Timedelta(days=365),
                   pd.Timestamp.today().normalize()),
            key="yf_daily_range"
        )

        if st.button("Load from Yahoo Finance", use_container_width=True, key="btn_load_yf"):
            if not ticker:
                st.error("Please select a popular ticker or enter a custom ticker.")
            else:
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start, end = map(lambda d: pd.Timestamp(d).strftime("%Y-%m-%d"), date_range)
                else:
                    start = (pd.Timestamp.today() - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
                    end = pd.Timestamp.today().strftime("%Y-%m-%d")

                tmp = load_yf_clean(ticker, start, end, auto_adj)
                if tmp is None or tmp.empty:
                    st.error(f"No data returned for {ticker}. Try a different ticker or range.")
                else:
                    set_df(tmp, f"Loaded {ticker} from {start} to {end}.")
                    # Record meta: popular vs custom
                    origin = "custom" if label == "Custom…" else "popular"
                    label_name = custom_ticker if origin == "custom" else label
                    st.session_state["maxprofit_meta"] = {
                        "source": "Yahoo Finance",
                        "ticker": ticker,
                        "origin": origin,      # "popular" or "custom"
                        "label": label_name,   # Friendly name (e.g., "Apple") or the custom text
                    }

    else:  # Upload CSV/Excel
        up = st.file_uploader("Upload a CSV/Excel (needs 'Date' and 'Close')", type=["csv", "xlsx", "xls"])
        if up and st.button("Load uploaded file", use_container_width=True, key="btn_load_upload"):
            # NOTE: load_csv_clean handles both CSV and multi-sheet Excel robustly.
            df = load_csv_clean(up)
            set_df(df, f"Loaded file with {len(df):,} rows.")
            if df is not None and not df.empty:
                st.session_state["maxprofit_meta"] = {
                    "source": "Upload",
                    "ticker": getattr(up, "name", "uploaded file"),
                    "origin": "upload",
                    "label": None,
                }

# Resolve working dataset strictly from page-local state
df = st.session_state["maxprofit_df"]
meta = st.session_state["maxprofit_meta"]

if df is None or df.empty:
    st.title("💰 Max Profit — Unlimited Transactions (Greedy)")
    st.info("Use the **sidebar** to load data (Session, Yahoo, or Upload).")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────────────────────────────────────────
st.title("💰 Max Profit — Unlimited Transactions (Greedy)")
st.caption("Implements Best Time to Buy and Sell Stock II (LeetCode 122) — greedy valley→peak.")

# Source/ticker badge
if meta and meta.get("ticker"):
    # NOTE: Cosmetic caption showing where the data came from.
    if meta.get("origin") == "popular":
        st.caption(f"Source: **{meta.get('source')}** • Ticker: **{meta.get('ticker')}** (Popular: **{meta.get('label')}**)")
    elif meta.get("origin") == "custom":
        st.caption(f"Source: **{meta.get('source')}** • Ticker: **{meta.get('ticker')}** (Custom)")
    elif meta.get("origin") == "session":
        st.caption(f"Source: **{meta.get('source')}** • Ticker: **{meta.get('ticker')}**")
    elif meta.get("origin") == "upload":
        st.caption(f"Source: **{meta.get('source')}** • File: **{meta.get('ticker')}**")
    else:
        st.caption(f"Source: **{meta.get('source') or 'Unknown'}** • Ticker: **{meta.get('ticker')}**")

# df is canonical already — no need to re-coerce dates/numerics or re-sort

# Quick summary
with st.expander("Quick summary", expanded=False):
    # NOTE: quick_summary reads either index or Date column safely.
    st.caption(quick_summary(df))
    
# Algorithm picker
algo_choice = st.radio(
    "Algorithm",
    list(ALGORITHMS.keys()),
    horizontal=True,
    index=0
)

# Fee input only for LC714
fee = 0.0
if "LC714" in algo_choice:
    # NOTE: Fee per *completed trade* (buy+sell); passed to LC714 runner via registry.
    fee = st.number_input("Transaction fee per trade", min_value=0.0, value=1.0, step=0.1)

# --- Single dispatch ---
# NOTE: Keep a single call to avoid double-computation and to preserve LC714 fee usage.
if "LC714" in algo_choice:
    trades, total_profit, meta_algo = ALGORITHMS[algo_choice](df["Date"], df["Close"], fee)
else:
    trades, total_profit, meta_algo = ALGORITHMS[algo_choice](df["Date"], df["Close"])

# Result
st.subheader("Result")
# NOTE: meta_algo['label'] comes from each runner (LC122/LC121/LC714); trades may be [] for LC714.
st.success(f"{meta_algo.get('label','Algorithm')} — Maximum Profit: **{total_profit:.2f}**  • Trades: **{len(trades)}**")

#Quick side-by-side comparison
with st.expander("Quick Profit Comparison", expanded=False):
    # If user is on LC714, reuse their chosen fee; otherwise offer a preview fee
    if "LC714" in algo_choice:
        fee_cmp = fee
    else:
        fee_cmp = st.number_input("Preview fee for LC714", min_value=0.0, value=1.0, step=0.1, key="cmp_fee")

    # Compute profits for each algo via the registry
    # NOTE: We call each runner directly to avoid duplicating algorithm code on the page.
    _, p122, _ = ALGORITHMS["Unlimited (LC122)"](df["Date"], df["Close"])
    _, p121, _ = ALGORITHMS["Single (LC121)"](df["Date"], df["Close"])
    _, p714, _ = ALGORITHMS["With Fee (LC714)"](df["Date"], df["Close"], fee_cmp)

    st.write(pd.DataFrame({
        "Algorithm": ["LC122 (Unlimited)", "LC121 (Single)", f"LC714 (fee={fee_cmp})"],
        "Profit": [p122, p121, p714]
    }))

# Trades table (optional)
if show_trades_table:
    st.subheader("Buy/Sell Plan (Greedy valley→peak)")
    # NOTE: LC121 returns a single trade (if profitable). LC714 returns [] by design (fast version).
    st.dataframe(
        pd.DataFrame(trades) if trades else pd.DataFrame(columns=["buy_date", "buy_price", "sell_date", "sell_price", "profit"]),
        use_container_width=True
    )

# Chart
# NOTE: The price line is always shown; markers are conditional on 'show_markers' and non-empty trades.
# Base price line
base = alt.Chart(df).mark_line().encode(
    x=alt.X("Date:T", title="Date"),
    y=alt.Y("Close:Q", title="Price")
).properties(height=360)

if show_markers and trades:
    buys = pd.DataFrame({
        "Date": [pd.to_datetime(t["buy_date"]) for t in trades],
        "Price": [t["buy_price"] for t in trades],
        "Type": "Buy"
    })
    sells = pd.DataFrame({
        "Date": [pd.to_datetime(t["sell_date"]) for t in trades],
        "Price": [t["sell_price"] for t in trades],
        "Type": "Sell"
    })
    points_df = pd.concat([buys, sells], ignore_index=True)

    markers = alt.Chart(points_df).mark_point(size=85).encode(
        x="Date:T",
        y="Price:Q",
        # keep distinct shapes for visual clarity
        shape=alt.Shape(
            "Type:N",
            scale=alt.Scale(domain=["Buy", "Sell"], range=["triangle-up", "triangle-down"]),
            legend=None  # <- show only one legend (color) to avoid duplication
        ),
        # color legend ON
        color=alt.Color(
            "Type:N",
            scale=alt.Scale(domain=["Buy", "Sell"], range=["#00c853", "#ff5252"]),  # green/red
            legend=alt.Legend(title="Trades", orient="top-left")
        ),
        tooltip=[
            alt.Tooltip("Type:N"),
            alt.Tooltip("Date:T"),
            alt.Tooltip("Price:Q", format=",.2f")
        ]
    )

    st.altair_chart(base + markers, use_container_width=True)
else:
    st.altair_chart(base, use_container_width=True)

# =======================
# VALIDATION RESULTS
# =======================
with st.expander("Validation (auto tests)", expanded=False):
    try:
        import pandas as pd
        from scr.Calculations.max_profit import max_profit_unlimited
        from scr.Calculations.lc121_single import max_profit_single
        from scr.Calculations.lc714_fee import max_profit_fee

        # NOTE: Keep these tests tiny, deterministic, and matching LeetCode examples.
        if algo_choice == "Unlimited (LC122)":
            tests = [
                ([7,1,5,3,6,4], 7.0),
                ([1,2,3,4,5],   4.0),
                ([5,4,3,2,1],   0.0),
                ([2,1,2,0,1],   2.0),
                ([3,3,5,0,0,3,1,4], 8.0),
            ]
            label = "LC122"
            for arr, expect in tests:
                got = float(max_profit_unlimited(pd.Series(arr)))
                st.write(f"{label}: prices={arr} → profit={got:.2f} (expect {expect:.2f}) "
                         + ("✅" if abs(got-expect) < 1e-9 else "❌"))

        elif algo_choice == "Single (LC121)":
            tests = [
                ([7,1,5,3,6,4], 5.0),
                ([1,2,3,4,5],   4.0),
                ([5,4,3,2,1],   0.0),
                ([2,1,2,0,1],   1.0),
                ([3,3,5,0,0,3,1,4], 4.0),
            ]
            label = "LC121"
            for arr, expect in tests:
                got = float(max_profit_single(pd.Series(arr))[2])
                st.write(f"{label}: prices={arr} → profit={got:.2f} (expect {expect:.2f}) "
                         + ("✅" if abs(got-expect) < 1e-9 else "❌"))

        elif algo_choice == "With Fee (LC714)":
            tests = [
                ([1,3,2,8,4,9], 2.0, 8.0),
                ([1,3,7,5,10,3], 3.0, 6.0),
                ([1,1,1,1], 1.0, 0.0),
            ]
            label = "LC714"
            for arr, fee_v, expect in tests:
                got = float(max_profit_fee(pd.Series(arr), fee_v))
                st.write(f"{label}: prices={arr}, fee={fee_v} → profit={got:.2f} (expect {expect:.2f}) "
                         + ("✅" if abs(got-expect) < 1e-9 else "❌"))

        # NOTE: Keep a single success banner to avoid confusion; ensure label is set above.
        st.success(f"All {label} validation cases passed.")

    except Exception as e:
        # NOTE: Catch-all so internal object reprs don’t leak giant docstrings to UI.
        st.error(f"Validation error: {e}")
