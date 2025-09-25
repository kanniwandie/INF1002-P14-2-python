# app/pages/4_Maximum Profit Calculation.py

# --- import shim for local dev ---
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ---------------------------------

import pandas as pd
import streamlit as st
import altair as alt

from scr.data.data_access import fetch_raw_yf, POPULAR_TICKERS
from scr.data.data_preprocessing import standardize_ohlcv, quick_summary
from scr.Calculations.max_profit import max_profit_unlimited
from scr.Calculations.trades import extract_trades  # your vectorized helper

st.set_page_config(page_title="Max Profit — Unlimited Transactions", layout="wide")

# =======================
# Cached loaders
# =======================
@st.cache_data(show_spinner=False)
def load_yf_clean(ticker: str, start: str, end: str, auto_adj: bool) -> pd.DataFrame:
    raw = fetch_raw_yf(ticker, start, end, auto_adjust=auto_adj)
    return standardize_ohlcv(raw).reset_index()  # ensure 'Date' column

@st.cache_data(show_spinner=False)
def load_csv_clean(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
    except Exception:
        df = pd.read_excel(file)

    # Parse Date
    if "Date" not in df.columns:
        for c in df.columns:
            if c.lower() in ("time", "timestamp"):
                df = df.rename(columns={c: "Date"})
                break
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Normalize column names
    rename_map = {c: c.capitalize() for c in df.columns if c.lower() in ["open","high","low","close","volume"]}
    df = df.rename(columns=rename_map)

    keep = [c for c in ["Date","Open","High","Low","Close","Volume"] if c in df.columns]
    if keep:
        df = df[keep]
    return df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)


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

    with st.expander("Advanced settings", expanded=False):
        auto_adj = st.checkbox("Auto-adjust prices (splits/dividends)", value=True,
                               help="Recommended when pulling from Yahoo Finance.")
        show_trades_table = st.checkbox("Show trades table", value=True)
        show_markers = st.checkbox("Show buy/sell markers on chart", value=True)

    # Basic controls vary by source
    df = None
    if source == "Session data":
        st.caption("Uses data already loaded on Home page.")
        if st.button("Use session data", use_container_width=True):
            if "data" in st.session_state and st.session_state["data"] is not None and not st.session_state["data"].empty:
                df = st.session_state["data"].copy()
                st.success("Loaded data from session.")
            else:
                st.warning("No session data found. Go to Home to load data first.")

    elif source == "Yahoo Finance":
        # Popular tickers + date range
        label = st.selectbox("Popular tickers", [name for name, _ in POPULAR_TICKERS])
        ticker = dict(POPULAR_TICKERS)[label]
        date_range = st.date_input(
            "Date range",
            value=(pd.Timestamp.today().normalize() - pd.Timedelta(days=365),
                   pd.Timestamp.today().normalize())
        )
        if st.button("Load from Yahoo Finance", use_container_width=True):
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start, end = map(lambda d: pd.Timestamp(d).strftime("%Y-%m-%d"), date_range)
            else:
                start = (pd.Timestamp.today() - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
                end = pd.Timestamp.today().strftime("%Y-%m-%d")
            tmp = load_yf_clean(ticker, start, end, auto_adj)
            if tmp is None or tmp.empty:
                st.error("No data returned. Try a different range.")
            else:
                df = tmp
                st.success(f"Loaded {ticker} from {start} to {end}.")

    else:  # Upload CSV/Excel
        up = st.file_uploader("Upload a CSV/Excel (needs 'Date' and 'Close')", type=["csv","xlsx","xls"])
        if up and st.button("Load uploaded file", use_container_width=True):
            tmp = load_csv_clean(up)
            if tmp is None or tmp.empty:
                st.error("Could not read usable columns. Ensure there is 'Date' and 'Close'.")
            else:
                df = tmp
                st.success(f"Loaded file with {len(df):,} rows.")

if df is None:
    if "data" in st.session_state and st.session_state["data"] is not None and not st.session_state["data"].empty:
        df = st.session_state["data"].copy()

if df is None or df.empty:
    st.title("💰 Max Profit — Unlimited Transactions (Greedy)")
    st.info("Use the **sidebar** to load data (Session, Yahoo Finance, or Upload).")
    st.stop()


# =======================
# MAIN AREA
# =======================
st.title("💰 Max Profit — Unlimited Transactions (Greedy)")

# Clean & validate columns
if "Date" not in df.columns or "Close" not in df.columns:
    st.error("Data must contain 'Date' and 'Close' columns.")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

close = pd.to_numeric(df["Close"], errors="coerce")
mask = close.notna()
df = df.loc[mask].reset_index(drop=True)
close = close.loc[mask].reset_index(drop=True)
dates = df["Date"].reset_index(drop=True)

# Quick summary
with st.expander("Quick summary", expanded=False):
    st.caption(quick_summary(df))

# Algorithm: core profit (float)
price_series = df.set_index("Date")["Close"].astype(float)
total_profit = float(max_profit_unlimited(price_series))

# Reconstruct greedy trades for explanation/plotting
trades = extract_trades(dates, close)

# Result
st.subheader("Result")
st.success(f"Maximum Profit: **{total_profit:.2f}**")

# Trades table (optional)
if show_trades_table:
    st.subheader("Buy/Sell Plan (Greedy valley→peak)")
    if trades:
        st.dataframe(pd.DataFrame(trades), use_container_width=True)
    else:
        st.info("No profitable trades found for this range.")

# Chart
base = alt.Chart(df).mark_line().encode(
    x=alt.X("Date:T", title="Date"),
    y=alt.Y("Close:Q", title="Price")
).properties(height=360)

if show_markers and trades:
    buy_points = pd.DataFrame(
        {"Date": [pd.to_datetime(t["buy_date"]) for t in trades],
         "Price": [t["buy_price"] for t in trades],
         "Type":  ["Buy"]*len(trades)}
    )
    sell_points = pd.DataFrame(
        {"Date": [pd.to_datetime(t["sell_date"]) for t in trades],
         "Price": [t["sell_price"] for t in trades],
         "Type":  ["Sell"]*len(trades)}
    )
    markers = alt.Chart(pd.concat([buy_points, sell_points], ignore_index=True)).mark_point(size=85).encode(
        x="Date:T",
        y="Price:Q",
        shape=alt.Shape("Type:N", legend=None),
        color=alt.Color("Type:N", legend=None),
        tooltip=[alt.Tooltip("Type:N"), alt.Tooltip("Date:T"), alt.Tooltip("Price:Q", format=",.2f")]
    )
    st.altair_chart(base + markers, use_container_width=True)
else:
    st.altair_chart(base, use_container_width=True)


