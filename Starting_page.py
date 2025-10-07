#  Starting_page.py
"""
Streamlit App: Stock Market Trend Analysis

This Streamlit application allows users to visualize and analyze stock market data 
over a selected time period. Users can choose from preset tickers or input a custom one. 
The app fetches data from Yahoo Finance, displays it, and enables exploration across 
different analytical pages such as SMA, Runs, Daily Returns, and Max Profit.


"""

import streamlit as st
from datetime import date, timedelta
from scr.data.yfinance_client import fetch_prices

# -----------------------------
# Preset list of popular tickers
# -----------------------------
TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA",
    "META", "TSLA", "NFLX", "AMD", "JPM", "KO", "V", "MCD", "DIS"
]

# -----------------------------
# Streamlit page configuration
# -----------------------------
st.set_page_config(page_title="Stock Market Trend Analysis", layout="wide")
st.title("📈 Stock Market Trend Analysis")

# -----------------------------
# Default settings and session initialization
# -----------------------------
today = date.today()
default_ticker = "AAPL"
default_end = today
default_start = today - timedelta(days=365 * 3)

# Initialize session state for persistence across pages
st.session_state.setdefault("cfg", {"ticker": default_ticker, "start": default_start, "end": default_end})
st.session_state.setdefault("data", None)
st.session_state.setdefault("meta", {"last_fetch_ok": False, "error": None})

# -----------------------------
# User controls for ticker and date selection
# -----------------------------
col_t, col_gap, col_start, col_end = st.columns([2.5, 0.3, 1.2, 1.2])

# --- Ticker selection ---
with col_t:
    ticker_choice = st.selectbox("Choose a ticker", TICKERS + ["Custom…"], index=0)
    if ticker_choice == "Custom…":
        # Allow custom ticker entry
        custom = st.text_input("Custom ticker (e.g., IBM)")
        ticker = custom.strip().upper() if custom else st.session_state["cfg"]["ticker"]
    else:
        ticker = ticker_choice

# --- Start date input ---
with col_start:
    start_date = st.date_input(
        "Start date",
        value=st.session_state["cfg"]["start"],
        min_value=date(2000, 1, 1),
        max_value=today
    )

# --- End date input ---
with col_end:
    end_date = st.date_input(
        "End date",
        value=st.session_state["cfg"]["end"],
        min_value=date(2000, 1, 2),
        max_value=today
    )

# -----------------------------
# Basic validation
# -----------------------------
if start_date > end_date:
    st.error("Start date cannot be after end date.")
    st.stop()

# -----------------------------
# Load data on button click
# -----------------------------
if st.button("Load Data", type="primary"):
    df = fetch_prices(ticker, start_date, end_date)

    if df is None or df.empty:
        # Handle empty or invalid fetch
        st.session_state["meta"] = {"last_fetch_ok": False, "error": "No data returned."}
        st.error("Failed to fetch data. Try another ticker or change the range.")
    else:
        # Save data and configuration in session
        st.session_state["cfg"] = {"ticker": ticker, "start": start_date, "end": end_date}
        st.session_state["data"] = df
        st.session_state["meta"] = {"last_fetch_ok": True, "error": None}
        st.success(f"Loaded {ticker}: {start_date} → {end_date}")

# -----------------------------
# Sidebar status information
# -----------------------------
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")

# -----------------------------
# Data preview table
# -----------------------------
df = st.session_state["data"]
if df is not None:
    st.subheader(f"Data Preview: {st.session_state['cfg']['ticker']}")
    st.dataframe(df.head(10), use_container_width=True)
