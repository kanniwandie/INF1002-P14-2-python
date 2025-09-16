import yfinance as yf
import pandas as pd

def fetch_prices(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch historical stock prices from Yahoo Finance.
    """
    df = yf.download(ticker, start=start, end=end, interval=interval)

    if df.empty:
        raise ValueError(f"No data found for {ticker} between {start} and {end}.")

    df.reset_index(inplace=True)

    expected_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = df[expected_cols]


    return df