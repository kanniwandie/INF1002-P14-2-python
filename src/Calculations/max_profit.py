import pandas as pd

def max_profit_from_df(df: pd.DataFrame, price_col: str = "Close") -> float:
    """
    Best Time to Buy and Sell Stock III (≤ 2 transactions).
    Works even if df[price_col] is a DataFrame instead of a Series.
    """
    if price_col not in df.columns:
        raise ValueError(f"Price column '{price_col}' not found. Available: {df.columns.tolist()}")

    # Ensure we always get a Series
    series = df[price_col]
    if isinstance(series, pd.DataFrame):
        # pick first column if duplicate
        series = series.iloc[:, 0]

    prices = pd.to_numeric(series, errors="coerce").dropna().to_list()
    if len(prices) < 2:
        return 0.0

    # Dynamic programming solution (≤ 2 transactions)
    buy1 = float("inf")
    profit1 = 0.0
    buy2 = float("inf")
    profit2 = 0.0

    for p in prices:
        buy1 = min(buy1, p)
        profit1 = max(profit1, p - buy1)
        buy2 = min(buy2, p - profit1)
        profit2 = max(profit2, p - buy2)

    return float(profit2)
