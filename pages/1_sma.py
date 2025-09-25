import streamlit as st
from src.Calculations.sma import compute_sma
from src.Visualization.sma_chart import plot_close_vs_sma

st.title("Simple Moving Average (SMA)")

if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data from the Home page first.")
else:
    df = st.session_state["data"]
    window = st.slider("Select SMA window size:", 2, 50, 5)
    sma_series = compute_sma(df["Close"], window)

    st.line_chart(sma_series)
    st.pyplot(plot_close_vs_sma(df, sma_series))
