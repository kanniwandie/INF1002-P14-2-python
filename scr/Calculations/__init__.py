# scr/Calculations/__init__.py
from __future__ import annotations
import pandas as pd
from scr.Calculations.max_profit import max_profit_unlimited, extract_trades
from scr.Calculations.lc121_single import run as run_121
from scr.Calculations.lc714_fee import run as run_714

def run_122(dates: pd.Series, prices: pd.Series) -> tuple[list[dict], float, dict]:
    """Wrap LC122 to match (trades, profit, meta) interface used by the UI."""
    price_series = pd.Series(pd.to_numeric(prices, errors="coerce").values,
                             index=pd.to_datetime(dates.values))
    total_profit = float(max_profit_unlimited(price_series))
    trades = extract_trades(dates, prices)
    meta = {"algo": "LC122", "label": "Unlimited Transactions"}
    return trades, total_profit, meta

ALGORITHMS = {
    "Unlimited (LC122)": run_122,
    "Single (LC121)": run_121,
    "With Fee (LC714)": run_714,
}
