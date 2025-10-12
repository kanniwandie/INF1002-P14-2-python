#scr/calculations/data/yfinance_client.py
# scr/calculations/data/yfinance_client.py
"""
Data Fetching Module
--------------------
This module provides a clean interface to download and standardize historical 
stock price data using the Yahoo Finance API (via `yfinance`). 

It ensures consistent column formatting, handles multi-indexed columns, 
and converts data types for reliability across downstream computations 
and visualizations.
"""

import yfinance as yf
import pandas as pd


def fetch_prices(ticker: str, start, end, interval: str = "1d") -> pd.DataFrame | None:
    """
    Fetch historical stock prices from Yahoo Finance and return a cleaned DataFrame.

    This function handles common issues such as empty responses, multi-index columns, 
    and inconsistent data types. The result is standardized to contain expected fields 
    like 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', and 'Volume'.

    Args:
        ticker (str): The stock ticker symbol (e.g., "AAPL", "MSFT").
        start (str or datetime): Start date for the data retrieval (e.g., "2023-01-01").
        end (str or datetime): End date for the data retrieval (e.g., "2023-12-31").
        interval (str, optional): Data sampling frequency. Defaults to "1d".
            Common options: "1d" (daily), "1wk" (weekly), "1mo" (monthly).

    Returns:
        pd.DataFrame | None: A cleaned DataFrame containing stock price data.
            Returns None if data is unavailable or an error occurs.
    """
    try:
        # Download data using Yahoo Finance API
        df = yf.download(
            tickers=ticker,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            group_by="column",   # Prevents multi-ticker column conflicts
            auto_adjust=False    # Keep raw close prices (no dividends/splits applied)
        )

        # Handle missing or invalid results
        if df is None or df.empty:
            return None

        # Some tickers return MultiIndex columns (e.g., ('Close', 'MSFT'))
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Reset index to make 'Date' a column
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])  # Ensure consistent datetime format

        # Convert all numeric columns to float (coerce invalid data to NaN)
        for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # Keep only the standard financial columns in consistent order
        keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in df.columns]
        return df[keep]

    except Exception as e:
        # Print error message for debugging without crashing the app
        print(f"Error fetching {ticker}: {e}")
        return None
