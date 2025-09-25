# scr/Calculations/max_profit.py
from __future__ import annotations
import pandas as pd
from typing import Union

def coerce_to_price_series(data: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    """
    Accept Series or DataFrame and return a numeric price Series.
    - If DataFrame: expects 'Close' and (optionally) 'Date' to set a DatetimeIndex.
    - If Series: returns numeric Series as-is (index may or may not be datetime).
    """
    if isinstance(data, pd.Series):
        return pd.to_numeric(data, errors="coerce").dropna()

    if isinstance(data, pd.DataFrame):
        df = data.copy()
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"]).set_index("Date").sort_index()
        if "Close" not in df.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")
        return pd.to_numeric(df["Close"], errors="coerce").dropna()

    raise TypeError("Input must be a pandas Series or DataFrame.")

def max_profit_unlimited(prices: Union[pd.Series, pd.DataFrame]) -> float:
    """
    Best Time to Buy and Sell Stock II (multiple transactions, hold ≤ 1 share).
    Returns a float profit. Keeps your original name/signature.
    """
    s = coerce_to_price_series(prices)
    # Greedy sum of positive differences (vectorized)
    diff = s.diff().fillna(0.0)
    profit = float(diff.where(diff > 0.0, 0.0).sum())
    return profit
