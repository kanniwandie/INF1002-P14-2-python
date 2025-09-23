import pandas as pd

def compute_sma(series: pd.Series, window: int = 5):
    return series.rolling(window=window).mean()
    