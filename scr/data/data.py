#scr/Calculations/data/data.py
"""
Data access layer for the project.

This module ONLY handles:
- picking/validating tickers & dates (optional helpers)
- downloading OHLCV data via yfinance
- returning a DataFrame with EXACTLY 6 headers:
  ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
- simple save/load utilities
"""

from __future__ import annotations
from typing import Optional, List, Tuple
import pandas as pd
import yfinance as yf

# --------------------------- public API --------------------------- #

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

def fetch_dataset(
    ticker: str,
    start: str,
    end: Optional[str] = None,
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """
    Download daily OHLCV from Yahoo Finance and return a dataframe with six headers:
    ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'].

    Notes
    -----
    - `auto_adjust=True` = Close is adjusted for splits/dividends.
    - No heavy cleaning here (your web/UI may do more). We only normalize columns.
    """
    df = yf.download(
        ticker,
        start=start,
        end=end or None,
        auto_adjust=auto_adjust,
        progress=False,
        group_by="column",    # avoids some MultiIndex cases
    )
    if df is None or df.empty:
        raise RuntimeError("No data returned. Check ticker or date range.")

    # Normalize the column names to Title Case (e.g., 'open' -> 'Open')
    df = df.rename(columns=str.title)

    # Ensure required columns exist (rare sources may miss one)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    for col in needed:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[needed]

    # Move DatetimeIndex into a 'Date' column and guarantee the name
    df = df.reset_index()
    if "Date" not in df.columns:
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)

    # Final order: exactly 6 headers
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    return df

def save_csv(df: pd.DataFrame, path: str) -> None:
    """Save the dataset to CSV (index disabled)."""
    df.to_csv(path, index=False)

def load_csv(path: str) -> pd.DataFrame:
    """Load a dataset from CSV, parsing the Date column."""
    return pd.read_csv(path, parse_dates=["Date"])

def dataset_summary(df: pd.DataFrame) -> str:
    """Return a short human-readable summary of the dataset."""
    n = len(df)
    first = df["Date"].min()
    last = df["Date"].max()
    return f"Rows: {n} | Range: {first.date()} → {last.date()}"

print(dataset_summary(fetch_dataset("AAPL", "2023-01-01", "2023-10-01")))
          
if __name__ == "__main__":
    # 1. Fetch dataset
    df = fetch_dataset("AAPL", "2023-01-01", "2023-10-01")

    # 2. Print headers
    print("\nHeaders:", df.columns.tolist())

    # 3. Print dataset summary
    print("Summary:", dataset_summary(df))

    # 4. Print first 5 rows
    print("\nFirst 5 rows:")
    print(df.head())

    # 5. Print last 5 rows
    print("\nLast 5 rows:")
    print(df.tail())

    # 6. Print number of rows
    print("\nNumber of rows:", len(df))

    # all
    print(df)
