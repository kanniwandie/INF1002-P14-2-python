# scr/Calculations/lc121_single.py
from __future__ import annotations
from typing import Tuple, List, Dict
import pandas as pd
from scr.Calculations.trades_utils import one_trade_as_rows

def max_profit_single(prices: pd.Series) -> Tuple[int, int, float]:
    """
    LeetCode 121 — Single transaction.
    Returns (buy_idx, sell_idx, profit). If no profit, (-1, -1, 0.0).
    """
    # Convert to numeric and drop NaNs to ensure consistent arithmetic
    s = pd.to_numeric(prices, errors="coerce").dropna()
    if s.empty:
        # No usable data — signal “no trade”
        return -1, -1, 0.0

    # Track the minimum price seen so far (and its index)
    min_price = float("inf")
    min_idx = -1

    # Track the best profit and corresponding buy/sell indices
    best_profit = 0.0
    b = sidx = -1

    # One pass O(n): for each day i, the best sell is p - min_so_far
    for i, p in enumerate(s.values):
        # If we found a new minimum, update the buy candidate
        if p < min_price:
            min_price = p
            min_idx = i
        else:
            # Candidate profit if selling today against the best min seen
            cand = p - min_price
            if cand > best_profit:
                best_profit = cand
                b, sidx = min_idx, i

    # If no positive profit found, report “no trade”
    if best_profit <= 0 or b < 0 or sidx < 0:
        return -1, -1, 0.0

    # Return indices relative to the numeric series s (not original df indices)
    return b, sidx, float(best_profit)

def run(dates: pd.Series, prices: pd.Series) -> tuple[list[dict], float, dict]:
    """
    Unified interface for the UI:
    Input: dates, prices
    Output: (trades_list, total_profit, meta)
    """
    # Compute the optimal single trade indices and profit
    b, sidx, profit = max_profit_single(prices)

    # Convert indices (b, sidx) into a row-friendly trade dict list for the UI table/markers.
    # If b or sidx are -1, one_trade_as_rows should return an empty list.
    trades: List[Dict] = one_trade_as_rows(dates, prices, b, sidx)

    # Provide a short label for the page's result banner
    meta = {"algo": "LC121", "label": "Single Transaction"}

    # Total profit equals the single best trade profit for LC121
    return trades, float(profit), meta
