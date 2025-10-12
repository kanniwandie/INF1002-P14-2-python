# pages/Daily Returns Page
"""
Streamlit Page: Daily Returns

This page computes the single-day percentage return r_t for a user-selected date
within the loaded dataset, using:
    r_t = (P_t - P_{t-1}) / P_{t-1}
where P_t is the Close price on the selected trading day. It also shows a line
chart of Close prices across the selected date range and preserves app status
in the sidebar.

"""

# pages/Daily Returns Page
import streamlit as st
import pandas as pd
from scr.Calculations.daily_returns import dr_calc

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="💹 Daily Returns")
st.title("💹 Daily Returns")

# -----------------------------
# Ensure dataset is retrieved
# -----------------------------

if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data from the Home page first.")
    st.stop()

# -----------------------------
# Date selection 
# -----------------------------
st.caption("Daily returns calculated using formula: rₜ = (Pₜ - Pₜ₋₁) / Pₜ₋₁ with daily **Close** prices.")
default_date = st.session_state["cfg"]["start"]
selected_date_custom = st.date_input(
    "Choose your date from loaded data range",
    value=default_date,
    min_value=st.session_state["cfg"]["start"],
    max_value=st.session_state["cfg"]["end"],
    format="YYYY-MM-DD"
)
dropdown_date = pd.Timestamp(selected_date_custom)

# -----------------------------
# Lookup & display selected day result
# -----------------------------

df = st.session_state["data"].copy()
matching_index = df.index[df["Date"] == dropdown_date]

st.subheader("Selected Date Details:")
sc, pc, dr = st.columns(3)

# -----------------------------
# Searching for date selected through dataset
# -----------------------------

if len(matching_index) > 0:
    index = matching_index[0]
    if index != 0:
        daily_return = dr_calc(df, index)
        sc.metric("Selected Close (Pₜ)",
                  f"${df.loc[index, 'Close']:.2f}", delta=None)
        pc.metric("Previous Close (Pₜ₋₁)",
                  f"${df.loc[index-1, 'Close']:.2f}", delta=None)
        dr.metric("Daily Return (rₜ)", f"{daily_return:.3f}%", delta=None)
    else:
        st.warning("No previous day to compare for daily return, please select range that starts earlier.")
else: 
    st.warning("No trading data for selected date, it could be a weekend or holiday. Please select another date.")

# -----------------------------
# Chart section
# -----------------------------
# Line chart for daily returns across the range of dates selected
st.subheader("Daily Returns for Range of Dates selected:")
st.line_chart(df, x="Date", y="Close", width=0, height=0, use_container_width=True)

# -----------------------------
# Sidebar status
# ----------------------------- 
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")

# -----------------------------
# Validation (auto tests)
# -----------------------------
import numpy as np

def _manual_rt(prev_close: float, curr_close: float) -> float:
    """
    Trusted baseline for r_t in percent:
        r_t = (P_t - P_{t-1}) / P_{t-1} * 100
    Returns NaN if prev_close is NaN/0 or if either value is missing.
    """
    if prev_close is None or curr_close is None:
        return np.nan
    if np.isnan(prev_close) or np.isnan(curr_close):
        return np.nan
    if prev_close == 0:
        return np.nan  # undefined
    return (curr_close - prev_close) / prev_close * 100.0

def _make_df_from_values(vals):
    """Build a minimal OHLCV-like DataFrame with Date/Close from a list of values (numbers or np.nan)."""
    temp = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=len(vals), freq="D"),
        "Close": pd.to_numeric(pd.Series(vals), errors="coerce")
    })
    return temp

def _try_dr_calc(df_local: pd.DataFrame, idx: int):
    """
    Safely call your implementation dr_calc(df, idx).
    If it raises or returns a non-numeric, return np.nan.
    """
    try:
        out = dr_calc(df_local, idx)
        return float(out) if out is not None else np.nan
    except Exception:
        return np.nan

def _validate_daily_return_cases(session_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare dr_calc() vs a trusted manual baseline across at least 5 cases,
    including corner cases.
    """
    cases = []

    # 1) Simple positive move
    df1 = _make_df_from_values([100, 110, 121])        # +10%, then +10%
    cases.append(("Simple +10%", df1, 1))
    cases.append(("Second +10% step", df1, 2))

    # 2) Negative move
    df2 = _make_df_from_values([50, 45])               # -10%
    cases.append(("Negative day -10%", df2, 1))

    # 3) Missing value in the middle (should yield NaN on that day)
    df3 = _make_df_from_values([10, np.nan, 12])
    cases.append(("Missing middle day", df3, 1))       # comparing against NaN baseline
    cases.append(("Day after missing", df3, 2))        # valid vs previous NaN → NaN

    # 4) First index (no previous day) should be undefined/NaN
    df4 = _make_df_from_values([200, 202])
    cases.append(("First index undefined", df4, 0))

    # 5) Real data slice from the loaded session (if available and long enough)
    #    Use the 10th row when possible; otherwise the last available index.
    if isinstance(session_df, pd.DataFrame) and len(session_df) >= 2:
        i = 10 if len(session_df) > 10 else len(session_df) - 1
        cases.append((f"Session data at idx={i}", session_df.reset_index(drop=True), i))

    # Evaluate
    rows = []
    for label, dfx, idx in cases:
        # Build baseline (manual) for that index
        prev_val = dfx.loc[idx - 1, "Close"] if idx > 0 else np.nan
        curr_val = dfx.loc[idx, "Close"]
        baseline = _manual_rt(prev_val, curr_val)

        # Your implementation
        got = _try_dr_calc(dfx, idx)

        # Compare with tolerance and NaN-equality
        if np.isnan(baseline) and np.isnan(got):
            passed = True
            max_abs_diff = 0.0
        else:
            passed = bool(np.isfinite(baseline) and np.isfinite(got) and abs(got - baseline) < 1e-9)
            max_abs_diff = float(abs(got - baseline)) if (np.isfinite(baseline) and np.isfinite(got)) else np.nan

        rows.append({
            "case": label,
            "index": idx,
            "prev_close": prev_val,
            "curr_close": curr_val,
            "baseline_%": baseline,
            "dr_calc_%": got,
            "passed": passed,
            "max_abs_diff": max_abs_diff
        })

    return pd.DataFrame(rows)

with st.expander("✅ Validation (auto tests)", expanded=False):
    results = _validate_daily_return_cases(df)

    # Summarize pass/fail
    for _, r in results.iterrows():
        check = "✅" if r["passed"] else "❌"
        st.write(f"{r['case']} → {check}  (baseline={r['baseline_%']}, got={r['dr_calc_%']}, |Δ|={r['max_abs_diff']})")

    if results["passed"].all():
        st.success("All daily return validation cases passed.")
    else:
        fails = results[~results["passed"]]
        st.error(f"{len(fails)} case(s) failed.")
        st.dataframe(fails, use_container_width=True)

    # Full table + CSV download
    st.markdown("#### Summary table")
    st.dataframe(results, use_container_width=True)
    st.download_button(
        "Download validation CSV",
        data=results.to_csv(index=False).encode("utf-8"),
        file_name="daily_return_validation_results.csv",
        mime="text/csv"
    )