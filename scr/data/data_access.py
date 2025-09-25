# scr/data/data_access.py
from __future__ import annotations
from typing import Optional, List, Tuple
import pandas as pd
import yfinance as yf

POPULAR_TICKERS: List[Tuple[str, str]] = [
    ("Apple", "AAPL"), ("Microsoft", "MSFT"), ("Amazon", "AMZN"),
    ("Alphabet (Class A)", "GOOGL"), ("NVIDIA", "NVDA"), ("Meta", "META"),
    ("Tesla", "TSLA"), ("Netflix", "NFLX"), ("AMD", "AMD"),
    ("Broadcom", "AVGO"), ("JPMorgan", "JPM"), ("Coca-Cola", "KO"),
    ("Visa", "V"), ("McDonald’s", "MCD"), ("Disney", "DIS"),
]

def fetch_raw_yf(
    ticker: str,
    start: str,
    end: Optional[str] = None,
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """
    Return the RAW yfinance DataFrame (DatetimeIndex; columns may include
    'Open','High','Low','Close','Adj Close','Volume', possibly MultiIndex).
    No schema guarantees. Use data_preprocessing.standardize_ohlcv(...) next.
    """
    df = yf.download(
        ticker, start=start, end=end or None,
        auto_adjust=auto_adjust, progress=False, group_by="column"
    )
    if df is None or df.empty:
        raise RuntimeError("No data returned. Check ticker or date range.")
    return df

# --- optional: keep legacy API name for existing code ---
def fetch_dataset(ticker: str, start: str, end: Optional[str] = None, auto_adjust: bool = True) -> pd.DataFrame:
    """
    Back-compat wrapper: fetch raw then return a canonical 6-col DataFrame with 'Date' col.
    Prefer using fetch_raw_yf + standardize_ohlcv() in new code.
    """
    from scr.data.data_preprocessing import standardize_ohlcv
    raw = fetch_raw_yf(ticker, start, end, auto_adjust=auto_adjust)
    df  = standardize_ohlcv(raw)                 # DatetimeIndex + OHLCV
    return df.reset_index().rename(columns={"index": "Date"})[["Date","Open","High","Low","Close","Volume"]]

def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)

def load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, parse_dates=["Date"])
    except Exception:
        return pd.read_csv(path)

def dataset_summary(df: pd.DataFrame) -> str:
    n = len(df)
    if "Date" in df.columns:
        first = pd.to_datetime(df["Date"]).min()
        last  = pd.to_datetime(df["Date"]).max()
    elif isinstance(df.index, pd.DatetimeIndex):
        first = df.index.min(); last = df.index.max()
    else:
        return f"Rows: {n}"
    return f"Rows: {n} | Range: {pd.to_datetime(first).date()} → {pd.to_datetime(last).date()}"
