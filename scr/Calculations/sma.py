#Scr/Calculations/sma.py
"""
SMA Utilities

Manual SMA computation for a univariate price series and a convenience
function that returns pandas' rolling mean for reference/validation.

"""

import pandas as pd
import numpy as np
def compute_sma(series: pd.Series, window: int = 5) -> pd.Series:
    """
    Compute the Simple Moving Average (SMA) for a one-dimensional numeric Series.

    The SMA at each index represents the average of the most recent `window` 
    observations. If there are fewer than `window` data points available, 
    the result is NaN for that position.

    Args:
        series (pd.Series): Input numeric series (e.g., stock closing prices) 
            in chronological order.
        window (int): The number of consecutive observations to average. 
            Must be a positive integer.

    Returns:
        pd.Series: A Series of SMA values aligned with the input index. 
        The first `window - 1` positions will be NaN due to insufficient data.

    Notes:
        - Use a positive integer for `window`; non-positive values are invalid.
        - This function does not coerce non-numeric values—ensure the input 
          Series is numeric before calling.
    """
    # Manually compute the Simple Moving Average (SMA).
    sma_values = [np.nan] * len(series)
    if window <= 0 or len(series) < window:
        return pd.Series(sma_values, index=series.index)

    # Initialize first window sum
    window_sum = series.iloc[:window].sum()
    sma_values[window - 1] = window_sum / window

    # Slide the window forward one step at a time
    for i in range(window, len(series)):
        window_sum += series.iloc[i] - series.iloc[i - window]  # add new, remove old
        sma_values[i] = window_sum / window

    return pd.Series(sma_values, index=series.index)


# ----Velidation for SMA function----
def valadate_sma(series: pd.Series, window: int = 5):
    """
    Reference SMA using pandas' rolling mean (baseline for validation).

    Args:
        series (pd.Series): Input numeric series.
        window (int): Window length passed to Series.rolling(window).mean().

    Returns:
        pd.Series: Pandas rolling mean with the same index as input.

    Note:
        The function name preserves the original spelling.
    """
    return series.rolling(window=window).mean()
