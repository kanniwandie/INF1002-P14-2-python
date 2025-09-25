# scr/data/yfinance_client.py
import yfinance as yf
import pandas as pd

def fetch_prices(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d",
    auto_adjust: bool = True,   # make the default explicit
) -> pd.DataFrame:
    """
    Fetch historical stock prices from Yahoo Finance and return a clean OHLCV frame.
    """
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=auto_adjust,   # explicit (avoids future-default surprises)
        progress=False,
        group_by="column",
    )

    if df is None or df.empty:
        raise ValueError(f"No data found for {ticker} between {start} and {end}.")

    # If yfinance returns a MultiIndex (rare with group_by), flatten it
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].title() for c in df.columns]
    else:
        df.columns = [str(c).title() for c in df.columns]

    df = df.reset_index()

    # Normalize expected columns; keep Adj Close fallback if Close missing
    if "Adj Close" in df.columns and "Close" not in df.columns:
        df.rename(columns={"Adj Close": "Close"}, inplace=True)
    if "date" in df.columns and "Date" not in df.columns:
        df.rename(columns={"date": "Date"}, inplace=True)

    expected_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        # If anything still missing, keep what we do have among expected
        keep = [c for c in expected_cols if c in df.columns]
        df = df[keep]
    else:
        df = df[expected_cols]

    return df
