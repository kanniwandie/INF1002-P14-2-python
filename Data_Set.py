# pull_dataset
from typing import Optional, List, Tuple
import pandas as pd
import yfinance as yf

# ------------------ Predefined Popular Stocks ------------------ #
# List of 15 popular stock tickers (with company names).
# User can pick from here or enter a custom ticker.
POPULAR: List[Tuple[str, str]] = [
    ("Apple", "AAPL"), ("Microsoft", "MSFT"), ("Amazon", "AMZN"),
    ("Alphabet (Class A)", "GOOGL"), ("NVIDIA", "NVDA"), ("Meta", "META"),
    ("Tesla", "TSLA"), ("Netflix", "NFLX"), ("AMD", "AMD"),
    ("Broadcom", "AVGO"), ("JPMorgan", "JPM"), ("Coca-Cola", "KO"),
    ("Visa", "V"), ("McDonald’s", "MCD"), ("Disney", "DIS"),
]

# ------------------ Menu to Pick Ticker ------------------ #
def pick_ticker() -> str:
    #Show menu of stocks and return chosen ticker symbol.
    print("\nPick a stock to analyze:")
    for i, (name, tkr) in enumerate(POPULAR, start=1):
        print(f"{i:>2}. {name} ({tkr})")
    print(" c. Custom ticker")

    # User input (defaults to option 1 → AAPL)
    choice = input("Enter a number (1–15) or 'c' [default 1]: ").strip().lower() or "1"

    if choice == "c":
        # Custom ticker path
        t = input("Enter a ticker symbol (e.g., AAPL): ").strip().upper()
        return t or "AAPL"

    try:
        # Convert number to index → return ticker symbol
        idx = int(choice) - 1
        return POPULAR[idx][1]
    except Exception:
        # If invalid input → fallback to AAPL
        print("Invalid choice → using AAPL.")
        return "AAPL"

# ------------------ Date Prompt ------------------ #
def prompt_date(label: str, default_iso: str) -> str:
    """
    Ask the user for a date (YYYY-MM-DD).
    If empty → use default.
    If invalid → fallback to default.
    """
    raw = input(f"{label} [default {default_iso}]: ").strip()
    if not raw:
        return default_iso
    try:
        return pd.to_datetime(raw, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        print("Unrecognized date. Using default.")
        return default_iso

# ------------------ Fetch Dataset ------------------ #
def fetch_dataset_simple(ticker: str, start: str, end: Optional[str]) -> pd.DataFrame:
    """
    Download daily OHLCV (Open, High, Low, Close, Volume) from Yahoo Finance.
    Normalize to 6 headers: Date, Open, High, Low, Close, Volume.
    """
    # Pull data (auto-adjust = True → adjust for splits/dividends)
    df = yf.download(ticker, start=start, end=end or None, auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise RuntimeError("No data returned. Check ticker or date range.")

    # Normalize column names (capitalize first letter)
    df = df.rename(columns=str.title)

    # Ensure required 5 numeric columns exist
    wanted = ["Open", "High", "Low", "Close", "Volume"]
    for col in wanted:
        if col not in df.columns:
            df[col] = pd.NA  # If missing, create with empty values

    # Keep only the wanted columns
    df = df[wanted]

    # Move index (DatetimeIndex) into a "Date" column
    df = df.reset_index()
    if "Date" not in df.columns:
        # Sometimes yfinance returns unnamed index → rename it
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)

    # Final reorder to guarantee exactly 6 headers
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    return df

# ------------------ Main Program ------------------ #
def main():
    # 1) Choose ticker
    ticker = pick_ticker()

    # 2) Get start & end dates (default → 2023-01-01 → today)
    default_start = "2023-01-01"
    default_end = pd.Timestamp.today().strftime("%Y-%m-%d")
    start = prompt_date("Start date", default_start)
    end = prompt_date("End date (press Enter for today)", default_end)

    # If user enters reversed dates (end < start) → swap them
    s_dt, e_dt = pd.to_datetime(start), pd.to_datetime(end)
    if e_dt < s_dt:
        print("End date is before start date. Swapping them.")
        start, end = e_dt.strftime("%Y-%m-%d"), s_dt.strftime("%Y-%m-%d")

    # 3) Fetch dataset
    print(f"\nDownloading {ticker} from {start} to {end} …")
    try:
        data = fetch_dataset_simple(ticker, start, end)
    except Exception as e:
        print(f"Error: {e}")
        return

    # 4) Show results
    print("\nHeaders:", data.columns.tolist())  # Show column names
    print(data)  # Print entire dataset (can be very long)

# ------------------ Run ------------------ #
if __name__ == "__main__":
    main()
