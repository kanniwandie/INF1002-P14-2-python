import streamlit as st
from datetime import timedelta, datetime
from scr.data.yfinance_client import fetch_prices
from scr.Calculations.daily_returns import dr_calc

st.set_page_config(
    page_title="Daily Returns"
)

default_date = datetime.date(2025, 1, 1)

selected_date_custom = st.date_input(
    "Choose your date",
    value=default_date,
    format="YYYY-MM-DD"
)
dropdown_date = selected_date_custom.strftime("%Y-%m-%d")

df = fetch_prices(dropdown_date, dropdown_date - timedelta(days=1), )
if dropdown_date in df["Date"]:
    index = df["Date"].index(dropdown_date)
    if index != 0:
        daily_return = dr_calc(index)
        st.write(f"Daily return for {dropdown_date}: {daily_return:.3f}%")
    else:
        st.write("Unable to calculate daily return")
else: 
    st.write("Unable to calculate daily return")