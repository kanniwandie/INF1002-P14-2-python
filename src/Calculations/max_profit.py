import pandas as pd
from typing import List, Tuple, Optional

Trade = Tuple[int, int, float]  # (buy_idx, sell_idx, profit)

def max_profit_with_trades(df: pd.DataFrame, price_col: str = "Close") -> Tuple[float, List[Trade]]:
    # Accept Series-like or 1-col DataFrame
    series = df.loc[:, price_col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    prices = pd.to_numeric(series, errors="coerce").dropna().to_list()
    if len(prices) < 2:
        return 0.0, []

    buy1_price = float("inf"); buy1_idx: Optional[int] = None
    sell1_profit = 0.0; sell1_buy_idx: Optional[int] = None; sell1_sell_idx: Optional[int] = None

    buy2_eff = float("inf"); buy2_idx: Optional[int] = None  # effective cost = price - sell1_profit at that moment
    sell2_profit = 0.0; sell2_buy_idx: Optional[int] = None; sell2_sell_idx: Optional[int] = None

    for i, p in enumerate(prices):
        # first buy
        if p < buy1_price:
            buy1_price = p
            buy1_idx = i

        # first sell
        cand1 = p - buy1_price
        if cand1 > sell1_profit and buy1_idx is not None:
            sell1_profit = cand1
            sell1_buy_idx = buy1_idx
            sell1_sell_idx = i

        # second buy (effective cost)
        eff = p - sell1_profit
        if eff < buy2_eff:
            buy2_eff = eff
            buy2_idx = i  # we conceptually "buy" here (using profit from the first trade)

        # second sell
        cand2 = p - buy2_eff
        if cand2 > sell2_profit and buy2_idx is not None:
            sell2_profit = cand2
            sell2_buy_idx = buy2_idx
            sell2_sell_idx = i

    if sell2_profit > sell1_profit and sell2_buy_idx is not None and sell2_sell_idx is not None:
        trades: List[Trade] = [(sell1_buy_idx, sell1_sell_idx, sell1_profit),
                               (sell2_buy_idx, sell2_sell_idx, sell2_profit - sell1_profit)]
        return sell2_profit, trades
    elif sell1_buy_idx is not None and sell1_sell_idx is not None:
        return sell1_profit, [(sell1_buy_idx, sell1_sell_idx, sell1_profit)]
    else:
        return 0.0, []
