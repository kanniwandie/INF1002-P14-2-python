# pages/2_Upward and Downward Runs.py

# --- Allow importing from project root when running from /pages ---
import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# -----------------------------------------------------------------

import streamlit as st
import pandas as pd

from scr.Calculations.updown_runs import compute_updown_runs

st.set_page_config(page_title="Upward & Downward Runs", layout="wide")
st.title("📈 Upward & Downward Runs")

# 1) Require data loaded by Home (main.py)
if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data on the Home page first.")
    st.stop()

df = st.session_state["data"]  # pass as-is
cfg = st.session_state.get("cfg", {})

# 2) Normalize column names defensively (fix common variations)
colmap = {}
if "Adj Close" in df.columns and "Close" not in df.columns:
    colmap["Adj Close"] = "Close"
if "date" in df.columns and "Date" not in df.columns:
    colmap["date"] = "Date"
if colmap:
    df.rename(columns=colmap, inplace=True)

need = {"Date", "Close"}
missing = need - set(df.columns)
if missing:
    st.error(f"Dataset missing required columns: {sorted(missing)}")
    st.stop()

# 3) Clean types
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
df = df.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)

# 4) Compute runs (no refetch; only use Home data)
with st.spinner("Computing runs…"):
    try:
        res = compute_updown_runs(df)
    except Exception as e:
        st.error(f"Failed to compute runs: {e}")
        st.stop()

# 3) Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Upward runs (count)", int(res["up_runs_count"]))
c2.metric("Downward runs (count)", int(res["down_runs_count"]))
c3.metric("Up-days total", int(res["up_days_total"]))
c4.metric("Down-days total", int(res["down_days_total"]))

# 4) Longest streaks
def _fmt_dt(x):
    try:
        return pd.to_datetime(x).date().isoformat()
    except Exception:
        return "—"

lu, ld = res["longest_up"], res["longest_down"]
c5, c6 = st.columns(2)
with c5:
    st.markdown("**Longest Upward Streak**")
    st.write(
        f"Length: **{lu['len']}**  \n"
        f"Start: **{_fmt_dt(lu['start'])}**  \n"
        f"End: **{_fmt_dt(lu['end'])}**"
    )
with c6:
    st.markdown("**Longest Downward Streak**")
    st.write(
        f"Length: **{ld['len']}**  \n"
        f"Start: **{_fmt_dt(ld['start'])}**  \n"
        f"End: **{_fmt_dt(ld['end'])}**"
    )

# 5) Detailed runs table
runs_df = res.get("runs")
if isinstance(runs_df, pd.DataFrame) and not runs_df.empty:
    pretty = runs_df.copy()
    pretty["start"] = pd.to_datetime(pretty["start"]).dt.date.astype("string")
    pretty["end"]   = pd.to_datetime(pretty["end"]).dt.date.astype("string")
    st.markdown("### Detailed Streaks")
    st.dataframe(pretty, width="stretch", height=360)
else:
    st.info("No streaks detected for the selected range.")

# 6) Footer status
ticker = cfg.get("ticker", "—")
start = cfg.get("start", "—")
end   = cfg.get("end", "—")
st.caption(f"Using dataset from Home: **{ticker}** | Range: **{start} → {end}**")

# Sidebar status (always visible)
with st.sidebar.expander("App status", expanded=True):
    cfg = st.session_state["cfg"]
    st.write(f"**Ticker:** {cfg['ticker']}")
    st.write(f"**Range:** {cfg['start']} → {cfg['end']}")
    st.write("Use the sidebar pages to explore SMA, Runs, Daily Returns, and Max Profit.")


