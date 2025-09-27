# src/Calculations/max_profit.py
from __future__ import annotations
from typing import Union, List, Dict
import numpy as np
import pandas as pd

# ---------- helpers ----------

def coerce_to_price_series(data: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    """
    Accept Series or DataFrame and return a numeric Close-price Series.
    - DataFrame: expects 'Close' and (optionally) 'Date' to set a DatetimeIndex.
    - Series: converted to numeric (index may or may not be datetime).
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

# ---------- algorithms ----------

def max_profit_unlimited(prices: Union[pd.Series, pd.DataFrame]) -> float:
    """
    Best Time to Buy and Sell Stock II (multiple transactions, hold ≤ 1 share).
    Greedy sum of positive day-to-day increases. Returns float profit.
    """
    s = coerce_to_price_series(prices)
    diff = s.diff().fillna(0.0)
    profit = float(diff.where(diff > 0.0, 0.0).sum())
    return profit

def extract_trades(dates: pd.Series, prices: pd.Series) -> List[Dict]:
    """
    Reconstruct greedy valley→peak trades from Date & Close arrays.
    Returns a list of dicts: {buy_date, buy_price, sell_date, sell_price, profit}
    """
    # Ensure alignment and float dtype
    s = pd.Series(prices).astype(float).reset_index(drop=True)
    dts = pd.to_datetime(pd.Series(dates), errors="coerce").reset_index(drop=True)

    # Day-to-day change and trend sign
    d = s.diff()
    sign = np.sign(d.fillna(0.0))

    # Resolve flat segments by forward-filling last non-zero sign
    nz = pd.Series(sign).replace(0, np.nan).ffill().fillna(0).values
    turn = pd.Series(nz).diff().fillna(0).values

    # Local minima where slope goes from <=0 to >0 (turn > 0)
    # Local maxima where slope goes from >=0 to <0 (turn < 0)
    minima_idx = np.where(turn > 0)[0]
    maxima_idx = np.where(turn < 0)[0]

    # Edge handling
    if len(minima_idx) == 0 or (len(maxima_idx) and minima_idx[0] > maxima_idx[0]):
        minima_idx = np.r_[0, minima_idx]  # treat start as valley if we begin rising
    if len(maxima_idx) == 0 or (len(minima_idx) and maxima_idx[-1] < minima_idx[-1]):
        maxima_idx = np.r_[maxima_idx, len(s) - 1]  # end peak if we finish rising

    # Pair valleys→peaks
    m = min(len(minima_idx), len(maxima_idx))
    minima_idx = minima_idx[:m]
    maxima_idx = maxima_idx[:m]

    trades: List[Dict] = []
    for buy_i, sell_i in zip(minima_idx, maxima_idx):
        if sell_i <= buy_i:
            continue
        buy_price = float(s.iloc[buy_i])
        sell_price = float(s.iloc[sell_i])
        if sell_price <= buy_price:
            continue
        trades.append({
            "buy_date": dts.iloc[buy_i].date(),
            "buy_price": buy_price,
            "sell_date": dts.iloc[sell_i].date(),
            "sell_price": sell_price,
            "profit": sell_price - buy_price
        })
    return trades
