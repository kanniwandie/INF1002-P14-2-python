# app/main.py

import streamlit as st

st.set_page_config(
    page_title="Stock Market Trend Analysis",
    page_icon="📊",
    layout="wide",
)

st.title("Stock Market Trend Analysis")
st.markdown(
    """
    Welcome to the **Stock Market Trend Analysis** project!  
    This tool helps you explore stock price trends with different calculations and visualizations.

    ### Features:
    - **SMA (Simple Moving Average):** View closing price vs. moving average.
    - **Upward & Downward Runs:** Detect consecutive streaks of gains/losses.
    - **Daily Returns:** Calculate simple daily returns.
    - **Max Profit (≤ 2 transactions):** Find the best times to buy & sell.
    - **Validation Results:** See comparisons with manual/test cases.

     Use the **sidebar** on the left to navigate between pages.
    """
)
