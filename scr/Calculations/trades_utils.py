# scr/Calculations/trades_utils.py
from __future__ import annotations
from typing import List, Dict
import pandas as pd

def one_trade_as_rows(dates: pd.Series, prices: pd.Series, b_idx: int, s_idx: int) -> List[Dict]:
    """Return a single trade in the same schema your page already displays."""
    # Guard clause: invalid indices or no profitable trade
    if b_idx < 0 or s_idx < 0:
        # Means no trade identified (e.g., LC121 found no profit opportunity)
        return []

    # Normalize and reindex dates/prices to ensure integer-based lookup
    dates = pd.to_datetime(dates).reset_index(drop=True)
    prices = pd.to_numeric(prices, errors="coerce").reset_index(drop=True)

    # Extract buy/sell prices for the given indices
    buy = float(prices.iloc[b_idx])
    sell = float(prices.iloc[s_idx])

    # Sanity check: ignore zero or negative-profit trades
    if not (sell > buy):
        return []

    # Return as list of dicts matching the Streamlit DataFrame schema:
    # ["buy_date","buy_price","sell_date","sell_price","profit"]
    # This format aligns with how `extract_trades` and LC121 results are displayed.
    return [{
        "buy_date": dates.iloc[b_idx].date(),
        "buy_price": buy,
        "sell_date": dates.iloc[s_idx].date(),
        "sell_price": sell,
        "profit": sell - buy
    }]
