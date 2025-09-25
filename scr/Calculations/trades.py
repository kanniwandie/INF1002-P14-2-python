# scr/Calculations/trades.py
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Dict

def extract_trades(dates: pd.Series, prices: pd.Series) -> List[Dict]:
    """
    Vectorized greedy trade reconstruction (valley→peak) for LeetCode-122 style.
    Produces the same pairs as a while-loop but via slope sign changes for originality.

    Parameters
    ----------
    dates : pd.Series (datetime-like)
    prices: pd.Series (float-like), same length and order as `dates`

    Returns
    -------
    List[Dict]: [
      {"buy_date": date, "buy_price": float,
       "sell_date": date, "sell_price": float, "profit": float}, ...
    ]
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
