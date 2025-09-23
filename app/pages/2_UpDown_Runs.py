# app/pages/2_UpDown_Runs.py
import streamlit as st
import pandas as pd
from src.Calculations.updown_runs import compute_updown_runs
from src.Visualization.run_chart import plot_runs

st.title("Upward & Downward Runs")

# Require global data from Home
if "data" not in st.session_state or st.session_state["data"] is None:
    st.warning("Please load data from the Home page first.")
    st.stop()

df = st.session_state["data"].copy()
df["Date"] = pd.to_datetime(df["Date"])

with st.spinner("Computing runs..."):
    res = compute_updown_runs(df)

# Metrics row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Upward runs (count)", res["up_runs_count"])
c2.metric("Downward runs (count)", res["down_runs_count"])
c3.metric("Up-days total", res["up_days_total"])
c4.metric("Down-days total", res["down_days_total"])

# Longest streaks
def _fmt_dt(x):
    try:
        return pd.to_datetime(x).date().isoformat()
    except Exception:
        return "—"

lu = res["longest_up"]
ld = res["longest_down"]
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

# Chart (highlight the longest of the two)
highlight = lu if lu["len"] >= ld["len"] else ld
st.pyplot(plot_runs(df, highlight=highlight))

# Optional detailed runs table
runs_df = res["runs"]
if isinstance(runs_df, pd.DataFrame) and not runs_df.empty:
    pretty = runs_df.copy()
    pretty["start"] = pd.to_datetime(pretty["start"]).dt.date.astype("string")
    pretty["end"]   = pd.to_datetime(pretty["end"]).dt.date.astype("string")
    st.markdown("### Detailed Streaks")
    st.dataframe(pretty, use_container_width=True, height=360)


