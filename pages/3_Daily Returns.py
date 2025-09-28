# pages/Daily Returns Page
import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from scr.data.yfinance_client import fetch_prices
from scr.Calculations.daily_returns import dr_calc

st.set_page_config(
    page_title="Daily Returns"
)

default_date = datetime(2025, 1, 1)

selected_date_custom = st.date_input(
    "Choose your date",
    value=default_date,
    format="YYYY-MM-DD"
)
dropdown_date = pd.Timestamp(selected_date_custom)

df = fetch_prices("AAPL", dropdown_date - timedelta(days=1), dropdown_date + timedelta(days=1))

matching_index = df.index[df["Date"] == dropdown_date]
dropdown_date_str = dropdown_date.strftime("%Y-%m-%d")

if len(matching_index) > 0:
    index = matching_index[0]
    if index != 0:
        daily_return = dr_calc(df, index)
        st.write(f"Daily return for {dropdown_date_str}: {daily_return:.3f}%")
    else:
        st.write("Unable to calculate daily return")
else: 
    st.write("Unable to calculate daily return")

<<<<<<< HEAD
df.columns = ['_'.join([str(level) for level in col if level]).strip() for col in df.columns]
st.line_chart(df, x="Date", y="Close_AAPL", width=0, height=0, use_container_width=True)
=======
# Sidebar status (always visible)
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")
>>>>>>> main
