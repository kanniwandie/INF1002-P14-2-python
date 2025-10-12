# pages/Daily Returns Page
"""
Streamlit Page: Daily Returns

This page computes the single-day percentage return r_t for a user-selected date
within the loaded dataset, using:
    r_t = (P_t - P_{t-1}) / P_{t-1}
where P_t is the Close price on the selected trading day. It also shows a line
chart of Close prices across the selected date range and preserves app status
in the sidebar.

"""

# pages/Daily Returns Page
import streamlit as st
import pandas as pd
from scr.Calculations.daily_returns import dr_calc

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="💹 Daily Returns")
st.title("💹 Daily Returns")

# -----------------------------
# Ensure dataset is retrieved
# -----------------------------

if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data from the Home page first.")
    st.stop()

# -----------------------------
# Date selection 
# -----------------------------
st.caption("Daily returns calculated using formula: rₜ = (Pₜ - Pₜ₋₁) / Pₜ₋₁ with daily **Close** prices.")
default_date = st.session_state["cfg"]["start"]
selected_date_custom = st.date_input(
    "Choose your date from loaded data range",
    value=default_date,
    min_value=st.session_state["cfg"]["start"],
    max_value=st.session_state["cfg"]["end"],
    format="YYYY-MM-DD"
)
dropdown_date = pd.Timestamp(selected_date_custom)

# -----------------------------
# Lookup & display selected day result
# -----------------------------

df = st.session_state["data"].copy()
matching_index = df.index[df["Date"] == dropdown_date]
dropdown_date_str = dropdown_date.strftime("%Y-%m-%d")

st.subheader("Selected Date Details:")
sc, pc, dr = st.columns(3)
# -----------------------------
# Searching for date selected through dataset

if len(matching_index) > 0:
    index = matching_index[0]
    if index != 0:
        daily_return = dr_calc(df, index)
        sc.metric("Selected Close (Pₜ)",
                  f"${df.loc[index, 'Close']:.2f}", delta=None)
        pc.metric("Previous Close (Pₜ₋₁)",
                  f"${df.loc[index-1, 'Close']:.2f}", delta=None)
        dr.metric("Daily Return (rₜ)", f"{daily_return:.3f}%", delta=None)
    else:
        st.warning("No previous day to compare for daily return, please select range that starts earlier.")
else: 
    st.warning("No trading data for selected date, it could be a weekend or holiday. Please select another date.")

# -----------------------------
# Chart section
# -----------------------------
# Line chart for daily returns across the range of dates selected
st.subheader("Daily Returns for Range of Dates selected:")
st.line_chart(df, x="Date", y="Close", width=0, height=0, use_container_width=True)

# -----------------------------
# Sidebar status
# ----------------------------- 
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")
