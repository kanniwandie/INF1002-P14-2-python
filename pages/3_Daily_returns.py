import streamlit as st
import pandas as pd
from src.Calculations.daily_returns import simple_returns, return_on_date

st.title("💹 Daily Returns (Close → Close)")

if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning(" Go to **Home** to pick a ticker & date range, then click **Load Data**.")
    st.stop()

df = st.session_state["data"].copy()
df["Date"] = pd.to_datetime(df["Date"])

# Ensure Close is a Series
close = df["Close"]
if isinstance(close, pd.DataFrame):
    close = close.squeeze(axis=1)

# Trading days (actual rows within range)
trading_days = df["Date"].dt.date.tolist()

st.caption("Formula: rₜ = (Pₜ − Pₜ₋₁) / Pₜ₋₁ using **Close** prices.")
sel_idx = st.selectbox(
    "Select a trading date from your loaded range:",
    options=list(range(len(trading_days))),
    format_func=lambda i: str(trading_days[i]),
    index=len(trading_days) - 1
)

sel_dt = trading_days[sel_idx]

# Full series for plotting
ret_series = simple_returns(close)
plot_df = pd.DataFrame({"Date": df["Date"], "Return": ret_series})
st.subheader("Daily Return Series")
st.line_chart(plot_df.set_index("Date"))

# Selected day summary
st.subheader("Selected Day Details")
summary = return_on_date(df, sel_dt)
col1, col2, col3 = st.columns(3)
col1.metric("Selected Close (Pₜ)", f"{summary.get('pt'):.2f}" if summary.get("pt") is not None else "—")
col2.metric("Previous Close (Pₜ₋₁)", f"{summary.get('pt_1'):.2f}" if summary.get("pt_1") is not None else "—")
col3.metric("rₜ", f"{summary.get('rt')*100:.2f}%" if summary.get("rt") is not None else "N/A (first day)")
