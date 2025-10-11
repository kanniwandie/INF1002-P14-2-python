# scr/Calcultions/data/data_preprocessing.py
from __future__ import annotations
import io
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
    Normalize ANY price dataset to OHLCV with a DatetimeIndex.
    - Flattens MultiIndex columns
    - Title-cases headers
    - Maps 'Adj Close'/'Price' -> 'Close' (if needed)
    - Ensures ['Open','High','Low','Close','Volume'] exist
    - Builds a DatetimeIndex from index/'Date'/first datelike col
    - Sorts, drops duplicate dates, minimal ffill/bfill, coerces numerics
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("standardize_ohlcv expects a pandas DataFrame")

    df = df.copy()

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Normalize header casing/spacing
    df.rename(columns={c: str(c).strip().title() for c in df.columns}, inplace=True)

    # Map common variations to Close
    if "Adj Close" in df.columns and "Close" not in df.columns:
        df.rename(columns={"Adj Close": "Close"}, inplace=True)
    if "Price" in df.columns and "Close" not in df.columns:
        df.rename(columns={"Price": "Close"}, inplace=True)

    # Ensure a DatetimeIndex
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
        df.index.name = df.index.name or "Date"
    elif "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).set_index("Date")
    else:
        if len(df.columns) > 0 and _is_datelike(df.iloc[:, 0]):
            col0 = df.columns[0]
            df[col0] = pd.to_datetime(df[col0], errors="coerce")
            df = df.dropna(subset=[col0]).set_index(col0)
            df.index.name = "Date"
        else:
            raise ValueError("No Date column or DatetimeIndex found (and could not infer one).")

    # Guarantee canonical columns
    for col in CANONICAL_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[CANONICAL_COLS]

    # Clean index & fill small gaps
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.ffill().bfill()

    # Coerce numerics
    for col in CANONICAL_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def to_price_series(df: pd.DataFrame) -> pd.Series:
    """Close as float Series with a DatetimeIndex (works with Date column or index)."""
    if isinstance(df.index, pd.DatetimeIndex):
        s = pd.to_numeric(df["Close"], errors="coerce").dropna()
        s.index = pd.to_datetime(df.index)
    else:
        s = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if "Date" in df.columns:
            s.index = pd.to_datetime(df.loc[s.index, "Date"], errors="coerce")
        else:
            s.index = pd.to_datetime(df.index, errors="coerce")
    s.index.name = "Date"
    return s

def quick_summary(df: pd.DataFrame) -> str:
    """One-line summary: row count and date range."""
    if df is None or df.empty:
        return "Rows: 0 | Range: N/A"
    start = end = None
    if isinstance(df.index, pd.DatetimeIndex) and len(df.index) > 0:
        start = df.index.min().date(); end = df.index.max().date()
    if (start is None or end is None) and "Date" in df.columns:
        d = pd.to_datetime(df["Date"], errors="coerce").dropna()
        if not d.empty:
            start = start or d.min().date(); end = end or d.max().date()
    return f"Rows: {len(df)} | Range: {start} → {end}" if start and end else f"Rows: {len(df)} | Range: N/A"

def load_file_clean(file_obj) -> pd.DataFrame:
    """
    Read CSV or Excel (uploaded file-like) and return standardized OHLCV with a 'Date' column.
    """
    try:
        buf = io.BytesIO(file_obj.read()) if hasattr(file_obj, "read") else file_obj
        df = pd.read_csv(buf)
    except Exception:
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            df = pd.read_excel(file_obj)
        except Exception:
            raise RuntimeError("Failed to read uploaded file as CSV or Excel.")
    df = standardize_ohlcv(df).reset_index()
    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]
