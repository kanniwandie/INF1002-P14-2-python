import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="📊 Live Stock Dashboard", layout="wide")

st.title("📊 Live Stock Dashboard")
st.caption("Real-time market snapshot for your selected ticker (from Yahoo Finance).")

# ---------------- Sidebar ---------------- #
with st.sidebar:
    st.header("Inputs")

    ticker = st.text_input("Enter a ticker symbol:", value="AAPL").upper()
    refresh_sec = st.slider("Auto-refresh interval (seconds)", 10, 300, 60, step=10)
    show_history = st.checkbox("Show intraday 1d chart", value=True)

# ---------------- Fetch Data ---------------- #
@st.cache_data(ttl=60)
def fetch_live_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info  # metadata (can be slow sometimes)
        df = stock.history(period="1d", interval="5m")
        return info, df
    except Exception as e:
        st.error(f"Failed to fetch data for {ticker}: {e}")
        return None, None

info, df = fetch_live_data(ticker)

if not info:
    st.stop()

# ---------------- Main Layout ---------------- #
c1, c2 = st.columns([2, 1])

# --- Left: Chart ---
with c1:
    st.subheader(f"{ticker} Intraday Price")
    if show_history and df is not None and not df.empty:
        chart_df = df.reset_index()[["Datetime", "Close"]]
        chart_df.rename(columns={"Datetime": "Time", "Close": "Price"}, inplace=True)
        chart_df["Time"] = pd.to_datetime(chart_df["Time"]).dt.strftime("%H:%M")
        st.line_chart(chart_df.set_index("Time"))
    else:
        st.info("No intraday data available.")

# --- Right: Snapshot ---
with c2:
    st.subheader("Snapshot")

    price = info.get("regularMarketPrice", "—")
    change = info.get("regularMarketChange", 0)
    pct = info.get("regularMarketChangePercent", 0)

    st.metric(
        label=f"{ticker} Price",
        value=f"{price:.2f}" if isinstance(price, (int, float)) else "—",
        delta=f"{change:.2f} ({pct:.2f}%)"
    )

    st.write("**At close:**", info.get("regularMarketPreviousClose", "—"))
    st.write("**Open:**", info.get("regularMarketOpen", "—"))
    st.write("**Day's range:**", f"{info.get('dayLow','—')} – {info.get('dayHigh','—')}")
    st.write("**52-week range:**", f"{info.get('fiftyTwoWeekLow','—')} – {info.get('fiftyTwoWeekHigh','—')}")
    st.write("**Volume:**", info.get("volume", "—"))
    st.write("**Market Cap:**", info.get("marketCap", "—"))
    st.write("**P/E (TTM):**", info.get("trailingPE", "—"))
    st.write("**EPS (TTM):**", info.get("trailingEps", "—"))
    st.write("**Forward Dividend & Yield:**", info.get("dividendYield", "—"))

# ---------------- Auto Refresh ---------------- #
st.caption(f"⏳ This dashboard refreshes every {refresh_sec} seconds.")
st.experimental_rerun()
