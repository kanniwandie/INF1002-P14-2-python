# scr/main.py
"""
CLI entry point (separate from the web UI).
- Choose ticker and date range
- Fetch dataset via Data.fetch_dataset
- Run one or more calculations from Calculation.py
"""

from __future__ import annotations
import pandas as pd
from Data import fetch_dataset, save_csv, dataset_summary, POPULAR_TICKERS
from Calculation import compute_sma  # <- you already have this

def pick_ticker_cli() -> str:
    print("\nPick a stock to analyze:")
    for i, (name, tkr) in enumerate(POPULAR_TICKERS, start=1):
        print(f"{i:>2}. {name} ({tkr})")
    print(" c. Custom ticker")
    choice = input("Enter a number (1–15) or 'c' [default 1]: ").strip().lower() or "1"
    if choice == "c":
        t = input("Enter ticker (e.g., AAPL): ").strip().upper()
        return t or "AAPL"
    try:
        idx = int(choice) - 1
        return POPULAR_TICKERS[idx][1]
    except Exception:
        print("Invalid choice → using AAPL.")
        return "AAPL"

def prompt_date(label: str, default_iso: str) -> str:
    raw = input(f"{label} [default {default_iso}]: ").strip()
    if not raw:
        return default_iso
    try:
        return pd.to_datetime(raw, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        print("Unrecognized date. Using default.")
        return default_iso

def main():
    # ---- 1) inputs ----
    ticker = pick_ticker_cli()
    default_start = "2023-01-01"
    default_end = pd.Timestamp.today().strftime("%Y-%m-%d")
    start = prompt_date("Start date", default_start)
    end = prompt_date("End date (press Enter for today)", default_end)

    # If user reverses dates, swap them (no heavy cleaning here)
    s_dt, e_dt = pd.to_datetime(start), pd.to_datetime(end)
    if e_dt < s_dt:
        print("End date is before start date. Swapping them.")
        start, end = e_dt.strftime("%Y-%m-%d"), s_dt.strftime("%Y-%m-%d")

    # ---- 2) fetch dataset ----
    print(f"\nDownloading {ticker} from {start} to {end} …")
    df = fetch_dataset(ticker, start, end)
    print("Dataset:", dataset_summary(df))

    # ---- 3) run calculations (example: SMA) ----
    try:
        win = int(input("SMA window [default 20]: ").strip() or "20")
    except Exception:
        win = 20
        print("Invalid SMA window, using 20.")
    sma = compute_sma(df["Close"], window=win)
    print(f"\nFirst 5 values of SMA({win}):")
    print(sma.head())

    # ---- 4) save CSV (optional) ----
    out_csv = f"../{ticker}.csv"  # save at project root (adjust as you like)
    save_csv(df, out_csv)
    print(f"\nSaved dataset to: {out_csv}")

if __name__ == "__main__":
    main()
