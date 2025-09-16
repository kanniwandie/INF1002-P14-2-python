import streamlit as st
import datetime
from scr.data.yfinance_client import df
from scr.Calculations.daily_returns import dr_date_list, dr_calc

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

if df["Date"] in dr_date_list:
    index = df["Date"].index(dropdown_date)
    if index != 0:
        daily_return = dr_calc(index)
        st.write(f"Daily return for {dropdown_date}: {daily_return:.3f}%")
    else:
        st.write("Unable to calculate daily return")
else: 
    st.write("Unable to calculate daily return")