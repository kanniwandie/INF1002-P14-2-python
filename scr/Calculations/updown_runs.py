# scr/Calculations/updown_runs.py
"""
Up/Down Runs Analysis

Computes sequences (“runs”) of consecutive up-days and down-days from Close-to-Close
changes in a price series. The function sanitizes input (coercing Date/Close types,
sorting by date, resetting index), returns summary metrics (counts, totals, longest
streaks), a detailed runs table, and a cleaned DataFrame ready for visualization.

Outputs (from compute_updown_runs):
- up_runs_count, down_runs_count (int)
- up_days_total, down_days_total (int)
- longest_up, longest_down: dicts with {"len","start","end","start_idx","end_idx"}
- runs: DataFrame columns ["dir","len","start","end","start_idx","end_idx"]
- clean_df: cleaned DataFrame with ["Date","Close"] for plotting


"""

from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd


def compute_updown_runs(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute consecutive up/down streaks from Close-to-Close changes.
    Flat days (no change) break any current streak.

    INPUT
    -----
    df : DataFrame with at least ["Date", "Close"] (can be messy; types are coerced here)

    RETURNS
    -------
    dict with:
      - up_runs_count : int
      - down_runs_count : int
      - up_days_total : int     # counts steps (price changes) in up runs
      - down_days_total : int   # counts steps (price changes) in down runs
      - longest_up : {"len": int, "start": Timestamp|None, "end": Timestamp|None,
                      "start_idx": int|None, "end_idx": int|None}
      - longest_down : same keys as longest_up
      - runs : DataFrame(columns=["dir", "len", "start", "end", "start_idx", "end_idx"])
      - clean_df : DataFrame with ["Date","Close"] cleaned, sorted, index reset  <-- NEW
    """
    # --- Clean & normalize input (this is now the single source of truth for viz too) ---
    data = df.copy()
    data["Date"] = pd.to_datetime(data.get("Date"), errors="coerce")
    data["Close"] = pd.to_numeric(data.get("Close"), errors="coerce")
    data = (
        data.dropna(subset=["Date", "Close"])
            .sort_values("Date")
            .reset_index(drop=True)
    )

    # Provide empty result if not enough rows
    if len(data) < 2:
        empty_runs = pd.DataFrame(columns=["dir", "len", "start", "end", "start_idx", "end_idx"])
        base = {
            "up_runs_count": 0,
            "down_runs_count": 0,
            "up_days_total": 0,
            "down_days_total": 0,
            "longest_up":   {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None},
            "longest_down": {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None},
            "runs": empty_runs,
            "clean_df": data[["Date", "Close"]] if not data.empty else pd.DataFrame(columns=["Date","Close"]),
        }
        return base

    closes = data["Close"].tolist()
    dates  = data["Date"].tolist()

    # Aggregates
    up_runs = down_runs = 0
    up_days_total = down_days_total = 0

    # Current streak
    cur_dir: str | None = None   # "up" | "down" | None
    cur_len = 0                  # number of steps in the streak
    cur_start_idx: int | None = None

    # Best streaks
    best_up  = {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None}
    best_down= {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None}

    # Collect all streaks
    runs_list: List[dict] = []

    def close_streak(end_idx: int):
        nonlocal cur_dir, cur_len, cur_start_idx
        nonlocal up_runs, down_runs, up_days_total, down_days_total, best_up, best_down, runs_list

        if cur_dir is None or cur_len == 0 or cur_start_idx is None:
            return

        start_dt = dates[cur_start_idx]
        end_dt   = dates[end_idx]
        runs_list.append({
            "dir": cur_dir,
            "len": cur_len,
            "start": start_dt,
            "end": end_dt,
            "start_idx": cur_start_idx,
            "end_idx": end_idx,
        })

        if cur_dir == "up":
            up_runs += 1
            up_days_total += cur_len
            if cur_len > best_up["len"]:
                best_up = {"len": cur_len, "start": start_dt, "end": end_dt,
                           "start_idx": cur_start_idx, "end_idx": end_idx}
        else:
            down_runs += 1
            down_days_total += cur_len
            if cur_len > best_down["len"]:
                best_down = {"len": cur_len, "start": start_dt, "end": end_dt,
                             "start_idx": cur_start_idx, "end_idx": end_idx}

        # reset
        cur_dir = None
        cur_len = 0
        cur_start_idx = None

    # Single pass over changes
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        step = "up" if delta > 0 else "down" if delta < 0 else None

        if step is None:
            # flat → break
            close_streak(i - 1)
            continue

        if cur_dir is None:
            cur_dir = step
            cur_len = 1
            cur_start_idx = i - 1
        elif cur_dir == step:
            cur_len += 1
        else:
            # direction flipped
            close_streak(i - 1)
            cur_dir = step
            cur_len = 1
            cur_start_idx = i - 1

    # close tail
    close_streak(len(closes) - 1)
    runs_df = pd.DataFrame(runs_list, columns=["dir", "len", "start", "end", "start_idx", "end_idx"])

    return {
        "up_runs_count": int(up_runs),
        "down_runs_count": int(down_runs),
        "up_days_total": int(up_days_total),
        "down_days_total": int(down_days_total),
        "longest_up": best_up,
        "longest_down": best_down,
        "runs": runs_df,
        "clean_df": data[["Date", "Close"]],   # <-- ready for plotting
    }
