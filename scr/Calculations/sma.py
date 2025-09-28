#Scr/Calculations/sma.py
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


# ----Velidation for SMA function----
def valadate_sma(series: pd.Series, window: int = 5):
    return series.rolling(window=window).mean()
