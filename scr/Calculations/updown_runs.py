# scr/Calculations/updown_runs.py
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd

def compute_updown_runs(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute consecutive up/down streaks from Close-to-Close changes.
    Flat days break any current streak.

    Returns a dict with:
      - up_runs_count, down_runs_count
      - up_days_total, down_days_total
      - longest_up  = {"len": int, "start": Timestamp|None, "end": Timestamp|None}
      - longest_down = same as above
      - runs (DataFrame with columns: dir, len, start, end)
    """
    # Ensure the dataframe has the required columns
    if not all(c in df.columns for c in ["Date", "Close"]):
        raise ValueError("DataFrame must contain 'Date' and 'Close'.")

    # --- Data cleaning and sorting ---
    # Make a copy to avoid mutating the original
    data = df.copy()

    # Convert 'Date' to datetime, invalid entries become NaT
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    # Convert 'Close' to numeric, invalid entries become NaN
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")

    # Drop rows where Date or Close is missing, sort chronologically
    data = data.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)
    # ---------------------------------

    # If there are fewer than 2 rows, no streaks can be computed
    if len(data) < 2:
        return {
            "up_runs_count": 0,
            "down_runs_count": 0,
            "up_days_total": 0,
            "down_days_total": 0,
            "longest_up":   {"len": 0, "start": None, "end": None},
            "longest_down": {"len": 0, "start": None, "end": None},
            "runs": pd.DataFrame(columns=["dir", "len", "start", "end"]),
        }

    # Extract lists for easier iteration
    closes = data["Close"].tolist()
    dates  = data["Date"].tolist()

    # Initialize counters
    up_runs = down_runs = 0
    up_days_total = down_days_total = 0

    # Track current streak
    cur_dir = None       # "up" | "down" | None
    cur_len = 0
    cur_start_idx = None

    # Track longest streaks
    best_up = {"len": 0, "start": None, "end": None}
    best_down = {"len": 0, "start": None, "end": None}

    # Store all streaks
    runs_list: List[dict] = []

    # Helper function: close the current streak and update stats
    def close_streak(end_idx: int):
        nonlocal cur_dir, cur_len, cur_start_idx
        nonlocal up_runs, down_runs, up_days_total, down_days_total, best_up, best_down, runs_list

        # If there is no active streak, do nothing
        if cur_dir is None or cur_len == 0:
            return

        # Record streak details
        start_dt = dates[cur_start_idx]
        end_dt   = dates[end_idx]
        runs_list.append({"dir": cur_dir, "len": cur_len, "start": start_dt, "end": end_dt})

        # Update stats depending on streak type
        if cur_dir == "up":
            up_runs += 1
            up_days_total += cur_len
            if cur_len > best_up["len"]:
                best_up = {"len": cur_len, "start": start_dt, "end": end_dt}
        else:
            down_runs += 1
            down_days_total += cur_len
            if cur_len > best_down["len"]:
                best_down = {"len": cur_len, "start": start_dt, "end": end_dt}

        # Reset current streak
        cur_dir = None
        cur_len = 0
        cur_start_idx = None

    # Iterate over all days, comparing consecutive Close prices
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        step = "up" if delta > 0 else "down" if delta < 0 else None

        if step is None:
            # flat day breaks any streak
            close_streak(i - 1)
            continue

        if cur_dir is None:
            # Start a new streak
            cur_dir = step
            cur_len = 1
            cur_start_idx = i - 1
        elif cur_dir == step:
            # Continue current streak
            cur_len += 1
        else:
            # direction flipped: close old streak and start new one
            close_streak(i - 1)
            cur_dir = step
            cur_len = 1
            cur_start_idx = i - 1

    # Close the last open streak if any
    close_streak(len(closes) - 1)

    # Convert streak list into DataFrame
    runs_df = pd.DataFrame(runs_list, columns=["dir", "len", "start", "end"])

    # Final results
    return {
        "up_runs_count": up_runs,
        "down_runs_count": down_runs,
        "up_days_total": up_days_total,
        "down_days_total": down_days_total,
        "longest_up": best_up,
        "longest_down": best_down,
        "runs": runs_df,
    }
