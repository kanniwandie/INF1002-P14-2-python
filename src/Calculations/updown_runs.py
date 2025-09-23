# src/Calculations/updown_runs.py
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd


def _as_series_close(close) -> pd.Series:
    """Coerce Close to a 1-D numeric Series."""
    if isinstance(close, pd.DataFrame):
        close = close.squeeze(axis=1)
    return pd.to_numeric(close, errors="coerce")


def compute_updown_runs(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze consecutive price *changes* (close-to-close) and return:
      - up_runs_count / down_runs_count
      - up_days_total / down_days_total
      - longest_up  = {'len', 'start', 'end', 'start_idx', 'end_idx'}
      - longest_down = {...}
      - runs: DataFrame with rows = each streak (type,len,start,end,start_idx,end_idx)

    Flat days (P_t == P_{t-1}) break streaks.
    """
    d = df.copy()
    d["Date"] = pd.to_datetime(d["Date"])
    close = _as_series_close(d["Close"])

    n = len(close)
    if n < 2:
        return {
            "up_runs_count": 0, "down_runs_count": 0,
            "up_days_total": 0, "down_days_total": 0,
            "longest_up": {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None},
            "longest_down": {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None},
            "runs": pd.DataFrame(columns=["type","len","start","end","start_idx","end_idx"])
        }

    runs: List[dict] = []
    cur_type = None          # 'up' or 'down'
    start_i = None           # start index (in df)
    up_runs_count = down_runs_count = 0
    up_days_total = down_days_total = 0

    # iterate deltas
    for i in range(1, n):
        delta = close.iloc[i] - close.iloc[i-1]
        if pd.isna(delta) or delta == 0:
            # close current streak if any
            if cur_type is not None and start_i is not None:
                end_i = i - 1
                length = end_i - start_i + 1
                runs.append({
                    "type": cur_type,
                    "len": length,
                    "start": d["Date"].iloc[start_i],
                    "end": d["Date"].iloc[end_i],
                    "start_idx": start_i,
                    "end_idx": end_i,
                })
                if cur_type == "up":
                    up_runs_count += 1
                    up_days_total += length
                else:
                    down_runs_count += 1
                    down_days_total += length
            cur_type, start_i = None, None
            continue

        step_type = "up" if delta > 0 else "down"
        if cur_type is None:
            cur_type = step_type
            start_i = i - 1
        elif step_type != cur_type:
            # close previous and start new
            end_i = i - 1
            length = end_i - start_i + 1
            runs.append({
                "type": cur_type,
                "len": length,
                "start": d["Date"].iloc[start_i],
                "end": d["Date"].iloc[end_i],
                "start_idx": start_i,
                "end_idx": end_i,
            })
            if cur_type == "up":
                up_runs_count += 1
                up_days_total += length
            else:
                down_runs_count += 1
                down_days_total += length
            cur_type = step_type
            start_i = i - 1
        else:
            # continue same streak
            pass

    # close tail
    if cur_type is not None and start_i is not None:
        end_i = n - 1
        length = end_i - start_i + 1
        runs.append({
            "type": cur_type,
            "len": length,
            "start": d["Date"].iloc[start_i],
            "end": d["Date"].iloc[end_i],
            "start_idx": start_i,
            "end_idx": end_i,
        })
        if cur_type == "up":
            up_runs_count += 1
            up_days_total += length
        else:
            down_runs_count += 1
            down_days_total += length

    runs_df = pd.DataFrame(runs)
    longest_up = {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None}
    longest_down = {"len": 0, "start": None, "end": None, "start_idx": None, "end_idx": None}
    if not runs_df.empty:
        up_rows = runs_df[runs_df["type"] == "up"]
        down_rows = runs_df[runs_df["type"] == "down"]
        if not up_rows.empty:
            idx = up_rows["len"].idxmax()
            row = runs_df.loc[idx]
            longest_up = {"len": int(row["len"]), "start": row["start"], "end": row["end"],
                          "start_idx": int(row["start_idx"]), "end_idx": int(row["end_idx"])}
        if not down_rows.empty:
            idx = down_rows["len"].idxmax()
            row = runs_df.loc[idx]
            longest_down = {"len": int(row["len"]), "start": row["start"], "end": row["end"],
                            "start_idx": int(row["start_idx"]), "end_idx": int(row["end_idx"])}

    return {
        "up_runs_count": int(up_runs_count),
        "down_runs_count": int(down_runs_count),
        "up_days_total": int(up_days_total),
        "down_days_total": int(down_days_total),
        "longest_up": longest_up,
        "longest_down": longest_down,
        "runs": runs_df
    }


# Backward-compat wrapper so older page code still works
def count_runs(series_like) -> dict:
    """Return minimal stats (legacy)."""
    s = _as_series_close(series_like)
    df = pd.DataFrame({"Date": pd.RangeIndex(len(s)), "Close": s})
    res = compute_updown_runs(df)
    return {
        "up_count": res["up_runs_count"],
        "down_count": res["down_runs_count"],
        "longest_up": res["longest_up"]["len"],
        "longest_down": res["longest_down"]["len"],
    }
