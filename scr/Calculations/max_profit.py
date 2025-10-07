# src/Calculations/max_profit.py

"""
Max Profit Utilities (Unlimited Transactions, Greedy)

This module provides utilities for computing the maximum achievable profit under
the “unlimited transactions, hold ≤ 1 share at a time” constraint (a.k.a.
LeetCode 122) and for reconstructing the corresponding buy/sell trades.

Key functions:
- max_profit_unlimited: O(n) greedy sum of positive day-to-day increases.
- extract_trades: Rebuilds valley→peak trade segments for explanation/plotting.
- coerce_to_price_series: Normalizes input (Series/DataFrame) into a numeric
  Close-price Series with an optional DatetimeIndex.

"""

from __future__ import annotations
from typing import Union, List, Dict
import numpy as np
import pandas as pd

# ---------- helpers ----------

def coerce_to_price_series(data: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    """
    Normalize input into a numeric Close-price Series.

    Accepts either a Series or a DataFrame and returns a 1-D numeric Series
    suitable for price-difference operations. If a DataFrame is provided and
    contains a 'Date' column, it will be parsed to datetime and set as the
    index (sorted ascending). NaNs in the resulting price vector are dropped.

    Args:
        data (pd.Series | pd.DataFrame): Input price container. For DataFrame,
            a 'Close' column is required; a 'Date' column (optional) will be
            parsed and used as a DatetimeIndex.

    Returns:
        pd.Series: Numeric Series of Close prices (index may be datetime if
            'Date' was present and valid).

    Raises:
        ValueError: If a DataFrame is provided without a 'Close' column.
        TypeError: If input is neither Series nor DataFrame.
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
    Compute the maximum profit with unlimited transactions (hold ≤ 1 share).

    Strategy:
        Greedy accumulation of all positive day-to-day price increases:
            profit = Σ max(0, p_t - p_{t-1})

    Complexity:
        O(n) time, O(1) extra space beyond the diff.

    Args:
        prices (pd.Series | pd.DataFrame): Price sequence or OHLCV frame. If a
            DataFrame is given, the 'Close' column is used (and 'Date' may set
            a DatetimeIndex).

    Returns:
        float: Total profit (non-negative).

    Notes:
        This assumes zero transaction costs and the ability to buy/sell within
        the same day transitions only (no shorting, one position at a time).
    """
    s = coerce_to_price_series(prices)
    diff = s.diff().fillna(0.0)
    profit = float(diff.where(diff > 0.0, 0.0).sum())
    return profit

def extract_trades(dates: pd.Series, prices: pd.Series) -> List[Dict]:
    """
    Reconstruct greedy valley→peak trades from aligned Date & Close arrays.

    The reconstruction pairs local minima (valleys) with subsequent local
    maxima (peaks) following the same greedy logic used by
    `max_profit_unlimited`. Flat segments are resolved by forward-filling the
    last non-zero slope sign to ensure deterministic turning points.

    Args:
        dates (pd.Series): Date-like sequence aligned with prices.
        prices (pd.Series): Close prices aligned with dates.

    Returns:
        list[dict]: Each dict contains:
            {
                "buy_date": date,
                "buy_price": float,
                "sell_date": date,
                "sell_price": float,
                "profit": float  # sell_price - buy_price
            }

    Notes:
        - Inputs are coerced to float prices and datetime-like dates internally.
        - Only strictly profitable segments (sell_price > buy_price) are kept.
        - Edge cases are handled so that a rising sequence at the start or end
          still yields a valid buy or sell respectively.
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
