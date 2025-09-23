import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.data.yfinance_client import fetch_prices
from src.Calculations.max_profit import max_profit

st.title("💰 Max Profit — LeetCode 122 (Multiple Transactions)")

# Require global config
if "cfg" not in st.session_state or "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Go to **Home** to choose a ticker & date range, then click **Load Data**.")
    st.stop()

cfg = st.session_state["cfg"]  # ticker / start / end

# --- Interval control (refetch only for this page if the user wants) ---
interval = st.selectbox("Data interval", ["1d", "1wk", "1mo"], index=0, help="Resamples prices from Yahoo Finance.")
refetch = st.checkbox("Refetch for this interval (recommended when changing interval)", value=True)

if refetch:
    df = fetch_prices(cfg["ticker"], cfg["start"], cfg["end"], interval=interval)
    if df is None or df.empty:
        st.error("No data returned for this interval. Try a different one.")
        st.stop()
else:
    df = st.session_state["data"].copy()

# --- Ensure tidy columns ---
df = df.copy()
df["Date"] = pd.to_datetime(df["Date"])
close = df["Close"]
if isinstance(close, pd.DataFrame):
    close = close.squeeze(axis=1)
close = pd.to_numeric(close, errors="coerce")
mask = close.notna()
df = df.loc[mask].reset_index(drop=True)
close = close.loc[mask].reset_index(drop=True)

# ---------- Greedy trade extraction: valley→peak pairs ----------
def extract_trades(dates: pd.Series, prices: pd.Series):
    """
    Build the exact buy/sell pairs that produce the LeetCode 122 greedy max profit.
    Returns a list of dicts: [{'buy_date', 'buy_price', 'sell_date', 'sell_price', 'profit'}, ...]
    """
    n = len(prices)
    trades = []
    i = 0
    while i < n - 1:
        # find next valley (local minimum)
        while i < n - 1 and prices[i+1] <= prices[i]:
            i += 1
        buy_i = i
        # find next peak (local maximum)
        while i < n - 1 and prices[i+1] >= prices[i]:
            i += 1
        sell_i = i
        if sell_i > buy_i:  # a valid trade
            buy_price = float(prices[buy_i])
            sell_price = float(prices[sell_i])
            trades.append({
                "buy_date": dates[buy_i].date(),
                "buy_price": buy_price,
                "sell_date": dates[sell_i].date(),
                "sell_price": sell_price,
                "profit": sell_price - buy_price
            })
        i += 1
    return trades

trades = extract_trades(df["Date"], close)
total = sum(t["profit"] for t in trades)

# Sanity: should equal standard LeetCode sum of positives
leetcode_total = max_profit(close.tolist())

st.markdown("Using **LeetCode 122** greedy method: sum of all positive close→close gains.")
st.success(f"Maximum Profit over selected range: **{total:.2f}**  "
           f"(greedy check: {leetcode_total:.2f})")

# --- Show trades table (if any) ---
if trades:
    tbl = pd.DataFrame(trades)
    st.subheader("Buy/Sell Plan (Greedy)")
    st.dataframe(tbl, use_container_width=True)
else:
    st.info("No profitable trades found for this range/interval.")

# --- Quick chart with markers ---
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(df["Date"], close.values, label="Close")
for t in trades:
    # buy marker
    ax.scatter(pd.to_datetime(t["buy_date"]), t["buy_price"], marker="^", s=70, label="_buy")
    # sell marker
    ax.scatter(pd.to_datetime(t["sell_date"]), t["sell_price"], marker="v", s=70, label="_sell")
ax.set_title(f"{cfg['ticker']} — Close with Greedy Buy/Sell Markers ({interval})")
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.legend(["Close"], loc="best")
st.pyplot(fig)
