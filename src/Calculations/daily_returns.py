import pandas as pd

def simple_returns(close: pd.Series) -> pd.Series:
    """
    Compute simple daily returns r_t = (P_t - P_{t-1}) / P_{t-1}
    using CLOSE-to-CLOSE prices.
    Returns a float Series aligned to the input index.
    """
    close = pd.to_numeric(close, errors="coerce")
    prev = close.shift(1)
    rt = (close - prev) / prev
    rt.name = "daily_return"
    return rt

def return_on_date(df: pd.DataFrame, dt) -> dict:
    """
    Given a DataFrame with columns ['Date','Close'] and a target date (datetime.date),
    return the selected day's close, previous day's close, and r_t.
    If the selected row is the first (no previous), r_t is None.
    """
    # Ensure Date is datetime64[ns]
    dates = pd.to_datetime(df["Date"]).dt.date
    if dt not in set(dates):
        return {"ok": False, "msg": "Selected date not in fetched range/trading days."}

    i = dates.tolist().index(dt)
    pt = float(df.loc[i, "Close"])
    if i == 0:
        return {"ok": True, "pt": pt, "pt_1": None, "rt": None}

    pt_1 = float(df.loc[i-1, "Close"])
    rt = (pt - pt_1) / pt_1 if pt_1 != 0 else None
    return {"ok": True, "pt": pt, "pt_1": pt_1, "rt": rt}
