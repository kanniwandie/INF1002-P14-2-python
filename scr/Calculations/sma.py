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
    Compute the Simple Moving Average (SMA) manually over a 1-D Series.

    For each index i:
        - If fewer than `window` observations are available (i + 1 < window),
          the result is NaN.
        - Otherwise, return the arithmetic mean of the last `window` values.

    Args:
        series (pd.Series): Input numeric series (e.g., Close prices) in
            chronological order.
        window (int): Window length for the moving average (>= 1 recommended).

    Returns:
        pd.Series: SMA series aligned to `series.index`, with NaN for the
        initial positions that lack enough history.

    Notes:
        - If `window` <= 0, this implementation will raise (e.g., division by
          zero). Use a positive integer window.
        - Non-numeric entries are not coerced; provide a numeric Series.
    """
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
