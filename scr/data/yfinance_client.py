#scr/calculations/data/yfinance_client.py
import yfinance as yf
import pandas as pd

def fetch_prices(ticker: str, start, end, interval: str = "1d") -> pd.DataFrame | None:
    try:
        df = yf.download(
            tickers=ticker,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            group_by="column",  # safer default
            auto_adjust=False
        )
        if df is None or df.empty:
            return None

        # Handle possible MultiIndex columns (e.g., ('Close','MSFT'))
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Standardize
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])
        # ensure numeric cols are numeric
        for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # Keep only expected columns if present
        keep = [c for c in ["Date","Open","High","Low","Close","Adj Close","Volume"] if c in df.columns]
        return df[keep]
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None
