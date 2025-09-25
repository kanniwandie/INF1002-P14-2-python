# data_preprocessing.py
"""
Lightweight preprocessing layer.
Goal: normalize any price dataset (yfinance, CSV, API) into a standard OHLCV
DataFrame with a DatetimeIndex so downstream algorithms don't break.
"""

import pandas as pd

CANONICAL_COLS = ["Open", "High", "Low", "Close", "Volume"]

def _is_datelike(series: pd.Series) -> bool:
    try:
        parsed = pd.to_datetime(series, errors="coerce")
        return parsed.notna().mean() > 0.8
    except Exception:
        return False

def standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize raw input into a clean OHLCV DataFrame.
    - Flattens MultiIndex columns if present
    - Renames common column variations
    - Ensures ['Open','High','Low','Close','Volume'] exist
    - Guarantees a DatetimeIndex (detects column or infers first date-like col)
    - Sorts index, drops duplicates
    - Fills missing values with forward-fill/backfill
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("standardize_ohlcv expects a pandas DataFrame")

    df = df.copy()

    # --- Flatten MultiIndex columns if present ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 1) Normalize header casing/spacing
    rename_map = {c: str(c).strip().title() for c in df.columns}
    df.rename(columns=rename_map, inplace=True)

    # 2) Handle common variations
    if "Adj Close" in df.columns and "Close" not in df.columns:
        df.rename(columns={"Adj Close": "Close"}, inplace=True)
    if "Price" in df.columns and "Close" not in df.columns:
        df.rename(columns={"Price": "Close"}, inplace=True)

    # 3) Ensure a DatetimeIndex (robust to different shapes)
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
        df.index.name = df.index.name or "Date"
    elif "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).set_index("Date")
    else:
        # try to infer a date column (common CSVs: first col is dates)
        if len(df.columns) > 0 and _is_datelike(df.iloc[:, 0]):
            col0 = df.columns[0]
            df[col0] = pd.to_datetime(df[col0], errors="coerce")
            df = df.dropna(subset=[col0]).set_index(col0)
            df.index.name = "Date"
        else:
            raise ValueError("No Date column or DatetimeIndex found (and could not infer one).")

    # 4) Guarantee canonical columns
    for col in CANONICAL_COLS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[CANONICAL_COLS]

    # 5) Clean index & fill gaps minimally
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.ffill().bfill()

    return df

def to_price_series(df: pd.DataFrame) -> pd.Series:
    """
    Extract Close price as a float series with DatetimeIndex.
    Downstream algorithms (like max_profit) consume this.
    """
    s = df["Close"].astype("float64")
    s.index = pd.to_datetime(df.index)
    s.index.name = "Date"
    return s

import pandas as pd

def quick_summary(df: pd.DataFrame) -> str:
    """
    Return a one-line summary: row count and date range.
    Works whether Date is an index (DatetimeIndex) or a column.
    """
    if df is None or df.empty:
        return "Empty DataFrame"

    start = end = "N/A"

    if isinstance(df.index, pd.DatetimeIndex) and len(df.index) > 0:
        try:
            start = df.index.min().date()
            end = df.index.max().date()
        except Exception:
            pass

    if (start == "N/A" or end == "N/A") and "Date" in df.columns:
        dates = pd.to_datetime(df["Date"], errors="coerce").dropna()
        if not dates.empty:
            start = dates.min().date()
            end = dates.max().date()

    return f"Rows: {len(df)} | Range: {start} → {end}"
