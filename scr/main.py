# scr/main.py
from __future__ import annotations
import pandas as pd

from Data import fetch_dataset, dataset_summary
from Calculations.daily_returns import daily_returns_series, daily_return_on_date


def main():
    # ---- 1) inputs (simple defaults for testing) ----
    ticker = input("Ticker [default AAPL]: ").strip().upper() or "AAPL"
    start = input("Start date [default 2023-01-01]: ").strip() or "2023-01-01"
    end = input("End date (Enter=today): ").strip() or None

    # ---- 2) fetch dataset ----
    print(f"\nDownloading {ticker} …")
    df = fetch_dataset(ticker, start, end)
    print("Dataset:", dataset_summary(df))

    # ---- 3) compute whole series of daily returns ----
    dr = daily_returns_series(df)
    df_out = df.copy()
    df_out["DailyReturn(%)"] = dr

    # Show a compact preview
    print("\n--- FIRST 5 ---")
    print(df_out.head(5))
    print("\n--- LAST 5 ---")
    print(df_out.tail(5))

    # ---- 4) compute daily return for a specific date ----
    query_date = input("\nEnter a trading date to check daily return [YYYY-MM-DD, Enter to skip]: ").strip()
    if query_date:
        val = daily_return_on_date(df, query_date)
        if val is None:
            print(f"No daily return available for {query_date} (not in dataset or first day).")
        else:
            print(f"Daily return for {query_date}: {val:.3f}%")

    # Optional: save to CSV for inspection
    out_csv = f"{ticker}_with_daily_returns.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"\nSaved with daily returns → {out_csv}")


if __name__ == "__main__":
    main()
