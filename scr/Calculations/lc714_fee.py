from __future__ import annotations
from typing import Tuple, List, Dict
import pandas as pd

def max_profit_fee(prices: pd.Series, fee: float) -> float:
    """
    LC714 — Max profit with transaction fee (O(n), DP).
    cash = max profit if we DO NOT hold a stock after day i
    hold = max profit if we DO hold a stock after day i
    """
    # Normalize inputs to numeric and drop missing values to avoid NaN math issues
    s = pd.to_numeric(prices, errors="coerce").dropna()
    if s.empty:
        # No usable data → zero profit
        return 0.0

    # DP states:
    # - cash: best profit with no position at end of day i
    # - hold: best profit while holding exactly one share at end of day i
    cash = 0.0
    hold = -float("inf")

    # Transition:
    # - Selling today:  cash = max(cash, hold + price - fee)
    # - Buying today:   hold = max(hold, prev_cash - price)
    for p in s.values:
        prev_cash = cash
        cash = max(cash, hold + p - fee)   # sell today (close position, pay fee)
        hold = max(hold, prev_cash - p)    # buy today (open/refresh position)

    # Final answer is the best state with no position (can't count an open position as realized profit)
    return float(cash)

def run(dates: pd.Series, prices: pd.Series, fee: float = 1.0) -> tuple[list[dict], float, dict]:
    """
    Unified interface for UI: (trades, total_profit, meta)
    """
    # Compute optimal fee-adjusted profit via the DP above
    total = max_profit_fee(prices, fee)

    # Keep metadata short; the page uses meta['label'] for the result banner
    meta = {"algo": "LC714", "label": f"With Transaction Fee (fee={fee})"}

    # Returning [] for trades keeps the UI consistent (table will show headers only for 714)
    return [], total, meta
