# src/Calculations/max_profit.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import pandas as pd

def max_profit_with_trades(df: pd.DataFrame,
                           price_col: str = "Close",
                           date_col: str = "Date"
                          ) -> Tuple[float, List[Dict]]:
    """
    LeetCode 123 (≤2 transactions), but also returns the exact trades.
    Returns:
      total_profit, trades where each trade is:
        {
          "buy_idx": int, "buy_date": Timestamp, "buy_price": float,
          "sell_idx": int, "sell_date": Timestamp, "sell_price": float,
          "profit": float
        }
    """
    # Accept Series or 1-col DataFrame
    series = df.loc[:, price_col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    prices = pd.to_numeric(series, errors="coerce").dropna().to_list()
    if len(prices) < 2:
        return 0.0, []

    # We'll track indices for each DP state
    buy1_price = float("inf"); buy1_idx: Optional[int] = None
    sell1_profit = 0.0; sell1_buy_idx: Optional[int] = None; sell1_sell_idx: Optional[int] = None

    buy2_eff = float("inf"); buy2_idx: Optional[int] = None  # effective cost = price - sell1_profit
    sell2_profit = 0.0; sell2_buy_idx: Optional[int] = None; sell2_sell_idx: Optional[int] = None

    for i, p in enumerate(prices):
        # first buy
        if p < buy1_price:
            buy1_price = p
            buy1_idx = i

        # first sell
        cand1 = p - buy1_price
        if buy1_idx is not None and cand1 > sell1_profit:
            sell1_profit = cand1
            sell1_buy_idx = buy1_idx
            sell1_sell_idx = i

        # second buy (effective cost uses best first-sell so far)
        eff = p - sell1_profit
        if eff < buy2_eff:
            buy2_eff = eff
            buy2_idx = i

        # second sell
        cand2 = p - buy2_eff
        if buy2_idx is not None and cand2 > sell2_profit:
            sell2_profit = cand2
            sell2_buy_idx = buy2_idx
            sell2_sell_idx = i

    trades: List[Dict] = []

    def build_trade(bi: int, si: int, base_profit_before: float = 0.0) -> Dict:
        return {
            "buy_idx":  bi,
            "buy_date": df.loc[bi, date_col],
            "buy_price": float(df.loc[bi, price_col] if not isinstance(df.loc[bi, price_col], pd.Series)
                               else df.loc[bi, price_col].iloc[0]),
            "sell_idx": si,
            "sell_date": df.loc[si, date_col],
            "sell_price": float(df.loc[si, price_col] if not isinstance(df.loc[si, price_col], pd.Series)
                                else df.loc[si, price_col].iloc[0]),
            "profit":   float((prices[si] - prices[bi]) - base_profit_before)
        }

    if sell2_profit > sell1_profit and sell1_buy_idx is not None and sell1_sell_idx is not None \
       and sell2_buy_idx is not None and sell2_sell_idx is not None:
        # two transactions
        t1 = build_trade(sell1_buy_idx, sell1_sell_idx, 0.0)
        # profit of second trade is (sell2_profit - sell1_profit)
        t2 = build_trade(sell2_buy_idx, sell2_sell_idx, sell1_profit)
        trades = [t1, t2]
        return float(sell2_profit), trades

    if sell1_buy_idx is not None and sell1_sell_idx is not None:
        # one transaction
        t1 = build_trade(sell1_buy_idx, sell1_sell_idx, 0.0)
        trades = [t1]
        return float(sell1_profit), trades

    return 0.0, []

# ---- NEW: return profit + actual trades (buy/sell date & price) ----
from typing import List, Dict, Optional, Tuple

def max_profit_with_trades(
    df: pd.DataFrame, price_col: str = "Close", date_col: str = "Date"
) -> Tuple[float, List[Dict]]:
    """
    LeetCode 123 (≤ 2 transactions), but also returns the actual trades:
      [
        {
          "buy_idx": int,  "buy_date": Timestamp, "buy_price": float,
          "sell_idx": int, "sell_date": Timestamp, "sell_price": float,
          "profit": float
        },
        ...
      ]
    """
    # get a clean list of prices
    series = df.loc[:, price_col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    prices = pd.to_numeric(series, errors="coerce").dropna().to_list()
    if len(prices) < 2:
        return 0.0, []

    # DP states + index tracking
    buy1_price = float("inf"); buy1_idx: Optional[int] = None
    sell1_profit = 0.0; sell1_buy_idx: Optional[int] = None; sell1_sell_idx: Optional[int] = None

    buy2_eff = float("inf"); buy2_idx: Optional[int] = None  # effective cost = price - sell1_profit
    sell2_profit = 0.0; sell2_buy_idx: Optional[int] = None; sell2_sell_idx: Optional[int] = None

    for i, p in enumerate(prices):
        # first buy
        if p < buy1_price:
            buy1_price = p
            buy1_idx = i

        # first sell
        cand1 = p - buy1_price
        if buy1_idx is not None and cand1 > sell1_profit:
            sell1_profit = cand1
            sell1_buy_idx = buy1_idx
            sell1_sell_idx = i

        # second buy (based on best first-sell so far)
        eff = p - sell1_profit
        if eff < buy2_eff:
            buy2_eff = eff
            buy2_idx = i

        # second sell
        cand2 = p - buy2_eff
        if buy2_idx is not None and cand2 > sell2_profit:
            sell2_profit = cand2
            sell2_buy_idx = buy2_idx
            sell2_sell_idx = i

    def _price_at(idx: int) -> float:
        val = df.loc[idx, price_col]
        return float(val if not isinstance(val, pd.Series) else val.iloc[0])

    def make_trade(bi: int, si: int, base_profit_before: float = 0.0) -> Dict:
        return {
            "buy_idx": bi,
            "buy_date": df.loc[bi, date_col],
            "buy_price": _price_at(bi),
            "sell_idx": si,
            "sell_date": df.loc[si, date_col],
            "sell_price": _price_at(si),
            "profit": float((prices[si] - prices[bi]) - base_profit_before),
        }

    trades: List[Dict] = []
    if (
        sell2_profit > sell1_profit
        and sell1_buy_idx is not None and sell1_sell_idx is not None
        and sell2_buy_idx is not None and sell2_sell_idx is not None
    ):
        t1 = make_trade(sell1_buy_idx, sell1_sell_idx, 0.0)
        t2 = make_trade(sell2_buy_idx, sell2_sell_idx, sell1_profit)
        trades = [t1, t2]
        return float(sell2_profit), trades

    if sell1_buy_idx is not None and sell1_sell_idx is not None:
        t1 = make_trade(sell1_buy_idx, sell1_sell_idx, 0.0)
        return float(sell1_profit), [t1]

    return 0.0, []
