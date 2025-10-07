# pages/2_Upward and Downward Runs.py
"""
Streamlit Page: Upward & Downward Runs

This page analyzes sequences of consecutive up-days and down-days (“runs”) in the
loaded price dataset. It computes counts, totals, longest streaks, shows a table
of all runs, and visualizes them with optional highlighting.

"""

# --- Allow importing from project root when running from /pages ---
import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# -----------------------------------------------------------------

import streamlit as st
import pandas as pd

from scr.Calculations.updown_runs import compute_updown_runs

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Upward & Downward Runs", layout="wide")
st.title("📈 Upward & Downward Runs")

# 1) Require data loaded by Home (main.py)
if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data on the Home page first.")
    st.stop()

df = st.session_state["data"]  # pass as-is
cfg = st.session_state.get("cfg", {})

# 2) Compute runs 
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
    """
    Safely format a datetime-like value to ISO date (YYYY-MM-DD).

    Args:
        x: A value convertible to pandas.Timestamp (or already a date-like).

    Returns:
        str: ISO-8601 date string if conversion succeeds, otherwise "—".
    """
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

from scr.Visualization.updown_chart import plot_updown_runs

# Use the cleaned, sorted df prepared by compute_updown_runs (Option 2)
clean_df = res["clean_df"]

# Let the user choose which streak to highlight
choice = st.radio(
    "Highlight:", ["Longest up", "Longest down", "None"],
    index=0, horizontal=True
)
highlight = None
if choice == "Longest up":
    highlight = res.get("longest_up")
elif choice == "Longest down":
    highlight = res.get("longest_down")

# Optional: toggle to show markers at segment edges
show_markers = st.checkbox("Show run boundary markers", value=False)

fig = plot_updown_runs(clean_df, highlight=highlight, show_markers=show_markers)
st.pyplot(fig)
