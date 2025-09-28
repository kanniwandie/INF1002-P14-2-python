# pages/Daily Returns Page
import streamlit as st
import pandas as pd
from scr.Calculations.daily_returns import dr_calc

st.set_page_config(
    page_title="💹 Daily Returns"
)
# Ensuring relevant data is retrieved 
if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data from the Home page first.")
    st.stop()

# Selection of date for daily returns
st.caption("Formula: rₜ = (Pₜ − Pₜ₋₁) / Pₜ₋₁ using daily **Close** prices.")
default_date = st.session_state["cfg"]["start"]
selected_date_custom = st.date_input(
    "Choose your date from loaded range",
    value=default_date,
    min_value=st.session_state["cfg"]["start"],
    max_value=st.session_state["cfg"]["end"],
    format="YYYY-MM-DD"
)
dropdown_date = pd.Timestamp(selected_date_custom)

df = st.session_state["data"].copy()
matching_index = df.index[df["Date"] == dropdown_date]
dropdown_date_str = dropdown_date.strftime("%Y-%m-%d")

# Searching for date selected through dataset
if len(matching_index) > 0:
    index = matching_index[0]
    if index != 0:
        daily_return = dr_calc(df, index)
        st.write(f"Daily return for {dropdown_date_str}: {daily_return:.3f}%")
    else:
        st.write("Unable to calculate daily return for starting date")
else: 
    st.write("Date out of range, unable to calculate daily return")

# Line chart for daily returns across the range of dates selected
st.subheader("Daily Returns for Range of Dates selected:")
st.line_chart(df, x="Date", y="Close", width=0, height=0, use_container_width=True)

# Sidebar status 
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")
