
# pages/1_sma.py i
"""
Streamlit Page: Simple Moving Average (SMA)

This page allows users to calculate and visualize the Simple Moving Average (SMA)
for their loaded stock price data. It provides an adjustable window size, displays
a comparative chart between closing prices and SMA, and validates the custom SMA 
implementation against pandas’ built-in rolling mean for correctness.

"""
import streamlit as st
import pandas as pd
import numpy as np

from scr.Calculations.sma import compute_sma
from scr.Visualization.sma_chart import plot_close_vs_sma  

# -----------------------------
# Page setup and header
# -----------------------------
st.set_page_config(page_title="SMA — Simple Moving Average", layout="wide")
st.title("📐 Simple Moving Average (SMA)")
st.caption("Compute SMA over your loaded price series. The validation below checks our implementation against a trusted baseline (pandas).")

# -----------------------------
# Ensure dataset is retrieved
# -----------------------------
if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data from the Home page first.")
    st.stop()

# Prepare dataset (convert types and clean)
df = st.session_state["data"].copy()
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
df = df.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)

# -----------------------------
# Controls: SMA window selection
# -----------------------------
left, mid, right = st.columns([1.2, 1, 1])

with left:
    window = st.slider("SMA window size", min_value=2, max_value=200, value=5, help="Number of days in each moving window.")

close = df["Close"]
sma_series = compute_sma(close, window)

with mid:
    st.metric("Data points", len(df))
with right:
    last_val = float(sma_series.dropna().iloc[-1]) if sma_series.notna().any() else np.nan
    st.metric(f"SMA{window} (last)", f"{last_val:.2f}" if not np.isnan(last_val) else "—")

# -----------------------------
# Chart visualization
# -----------------------------
st.pyplot(plot_close_vs_sma(df, sma_series))

# -----------------------------
# SMA Validation Function
# -----------------------------
def _validate_sma_cases(df: pd.DataFrame, user_window: int) -> pd.DataFrame:
    """
    Validate the custom compute_sma() function by comparing its results with pandas.rolling().mean().

    Args:
        df (pd.DataFrame): DataFrame containing price data.
        user_window (int): User-selected window size for SMA.

    Returns:
        pd.DataFrame: Summary of validation test results including case name, window, 
                      pass/fail status, and maximum absolute difference.
    """
    # Build validation test cases
    tests = [
        {"case": "Ascending 1..10, w=3", "series": pd.Series(range(1, 11)), "w": 3},
        {"case": "Shorter than window, w=5", "series": pd.Series([10, 20, 30, 40]), "w": 5},
        {"case": "With NaNs, w=0", "series": pd.Series([10, np.nan, 30, 40, 50]), "w": 0},
        {"case": "Window=1 (identity)", "series": pd.Series([5, 7, 9, 11]), "w": 1},
        {"case": "Constant series, w=4", "series": pd.Series([7] * 8), "w": 4},
        {"case": "Window equals length, w=4", "series": pd.Series([2, 4, 6, 8]), "w": 4},
        {"case": "Real data slice (first 30)", "series": df["Close"].head(30).reset_index(drop=True), "w": user_window},
    ]

    # Compare compute_sma vs pandas rolling mean
    rows = []
    for t in tests:
        mine = compute_sma(t["series"], t["w"])
        ref  = t["series"].rolling(window=t["w"]).mean()  # trusted baseline

        # Evaluate results, allowing NaN matches
        passed = bool(np.allclose(mine.to_numpy(dtype=float), ref.to_numpy(dtype=float), equal_nan=True))

        # Compute maximum absolute difference
        diff = (mine - ref).abs()
        max_abs_diff = float(diff.dropna().max()) if diff.notna().any() else 0.0

        rows.append({"case": t["case"], "window": t["w"], "passed": passed, "max_abs_diff": round(max_abs_diff, 10)})
    return pd.DataFrame(rows)

# -----------------------------
# Validation Results Display
# -----------------------------
with st.expander("✅ Validation (auto tests)", expanded=False):
    results = _validate_sma_cases(df, window)

    # Display pass/fail summary
    for _, r in results.iterrows():
        check = "✅" if r["passed"] else "❌"
        st.write(f"{r['case']} → {check}  (max |Δ| = {r['max_abs_diff']})")

    # Overall status message
    if results["passed"].all():
        st.success("All validation cases passed.")
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
        file_name="sma_validation_results.csv",
        mime="text/csv"
    )

# -----------------------------
# Sidebar Status
# -----------------------------
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state.get("cfg", {})
    st.write(f"**Ticker:** {cfg.get('ticker','—')}")
    st.write(f"**Range:** {cfg.get('start','—')} → {cfg.get('end','—')}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")
