# pages/4_Maximum Profit Calculation.py

import pandas as pd
import streamlit as st
import altair as alt

from scr.data.data import fetch_raw_yf, POPULAR_TICKERS
from scr.data.data_preprocessing import standardize_ohlcv, quick_summary
from scr.Calculations.max_profit import max_profit_unlimited, extract_trades

st.set_page_config(page_title="Max Profit — Unlimited Transactions", layout="wide")

# -----------------------
# Page-local state
# -----------------------
st.session_state.setdefault("maxprofit_df", None)
st.session_state.setdefault("maxprofit_source", None)
st.session_state.setdefault("maxprofit_meta", {"source": None, "ticker": None, "origin": None, "label": None})

# -----------------------
# Helpers
# -----------------------
def canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    """Run once to enforce Date/Open/High/Low/Close/Volume, sorted unique dates."""
    return standardize_ohlcv(df).reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]

@st.cache_data(show_spinner=False)
def load_yf_clean(ticker: str, start: str, end: str, auto_adj: bool) -> pd.DataFrame:
    raw = fetch_raw_yf(ticker, start, end, auto_adjust=auto_adj)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    return canonicalize(raw)

@st.cache_data(show_spinner=False)
def load_csv_clean(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
    except Exception:
        try:
            if hasattr(file, "seek"):
                file.seek(0)
        except Exception:
            pass
        df = pd.read_excel(file)
    return canonicalize(df)

def set_df(df: pd.DataFrame, ok_msg: str):
    if df is None or df.empty:
        st.error("No data returned.")
    else:
        st.session_state["maxprofit_df"] = df
        st.success(ok_msg)

# =======================
# SIDEBAR
# =======================
with st.sidebar:
    st.header("Data Controls")

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

    with st.expander("Advanced settings", expanded=False):
        auto_adj = st.checkbox("Auto-adjust prices (splits/dividends)", value=True)
        show_trades_table = st.checkbox("Show trades table", value=True)
        show_markers = st.checkbox("Show buy/sell markers on chart", value=True)

    df = None

    if source == "Session data":
        st.caption("Uses data already loaded on Home page.")
        if st.button("Use session data", use_container_width=True, key="btn_use_sess"):
            if "data" in st.session_state and isinstance(st.session_state["data"], pd.DataFrame) and not st.session_state["data"].empty:
                df = canonicalize(st.session_state["data"])
                set_df(df, "Loaded session snapshot.")
                if df is not None and not df.empty:
                    tick = st.session_state.get("cfg", {}).get("ticker", "Unknown")
                    st.session_state["maxprofit_meta"] = {
                        "source": "Session data",
                        "ticker": tick,
                        "origin": "session",
                        "label": None,
                    }
            else:
                st.warning("No session data found. Go to Home to load data first.")

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

# =======================
# MAIN AREA
# =======================
st.title("💰 Max Profit — Unlimited Transactions (Greedy)")
st.caption("Implements Best Time to Buy and Sell Stock II (LeetCode 122) — greedy valley→peak.")


# Source/ticker badge
if meta and meta.get("ticker"):
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
    st.caption(quick_summary(df))

# Algorithm: core profit (float)
price_series = df.set_index("Date")["Close"].astype(float)
total_profit = float(max_profit_unlimited(price_series))

# Reconstruct greedy trades for explanation/plotting
trades = extract_trades(df["Date"], df["Close"])

# Result
st.subheader("Result")
st.success(f"Maximum Profit: **{total_profit:.2f}**  • Trades: **{len(trades)}**")


# Trades table (optional)
if show_trades_table:
    st.subheader("Buy/Sell Plan (Greedy valley→peak)")
    st.dataframe(
        pd.DataFrame(trades) if trades else pd.DataFrame(columns=["buy_date", "buy_price", "sell_date", "sell_price", "profit"]),
        use_container_width=True
    )

# Chart
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
    markers = alt.Chart(pd.concat([buys, sells], ignore_index=True)).mark_point(size=85).encode(
        x="Date:T", y="Price:Q",
        shape=alt.Shape("Type:N", legend=None),
        color=alt.Color("Type:N", legend=None),
        tooltip=[alt.Tooltip("Type:N"), alt.Tooltip("Date:T"), alt.Tooltip("Price:Q", format=",.2f")]
    )
    st.altair_chart(base + markers, use_container_width=True)
else:
    st.altair_chart(base, use_container_width=True)

# =======================
# VALIDATION RESULTS
# =======================
with st.expander("Validation (auto tests)", expanded=False):
    tests = [
        ([7,1,5,3,6,4], 7.0),
        ([1,2,3,4,5],   4.0),
        ([5,4,3,2,1],   0.0),
        ([2,1,2,0,1],   2.0),
        ([3,3,5,0,0,3,1,4], 8.0),
    ]
    ok = True
    for arr, expect in tests:
        s = pd.Series(arr, index=pd.date_range("2020-01-01", periods=len(arr)))
        got = float(max_profit_unlimited(s))
        st.write(
            f"prices={arr} → profit={got:.2f} (expect {expect:.2f}) "
            + ("✅" if abs(got-expect) < 1e-9 else "❌")
        )
        ok &= abs(got-expect) < 1e-9

    if ok:
        st.success("All validation cases passed.")
    else:
        st.error("Some validation cases failed.")

# Sidebar status (always visible)
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")

