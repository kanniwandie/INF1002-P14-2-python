"""
Pls move this set of code to scr/Calculations/sma.py
as this is not for the page file.
"""
# import pandas as pd

# def compute_sma(series: pd.Series, window: int = 5):
#     return series.rolling(window=window).mean()

import pandas as pd
import numpy as np

def compute_sma(series: pd.Series, window: int = 5) -> pd.Series:
    # Manually compute the Simple Moving Average (SMA).
    sma_values = []
    for i in range(len(series)):
        if i + 1 < window:
            sma_values.append(np.nan)  # not enough data
        else:
            window_vals = series[i + 1 - window : i + 1]  # last window values
            sma_values.append(window_vals.sum() / window)
    return pd.Series(sma_values, index=series.index)

# Sidebar status (always visible)
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")
