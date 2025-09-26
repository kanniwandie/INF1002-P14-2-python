# import streamlit as st
# import pandas as pd
# import numpy as np
# from datetime import datetime

# st.set_page_config(page_title="✅ Validation Results", layout="wide")
# st.title("✅ Validation Results")
# st.caption(
#     "This page validates our financial computations against trusted / independent references. "
#     "By default we do **not** call the app’s own functions; we compute reference results using "
#     "distinct methods (prefix sums, vectorization, DP). Use the optional toggle to compare against "
#     "your implementation for pass/fail summaries."
# )

# # Utility: try to import project implementations ONLY if the user turns on comparison
# def try_import_my_impl():
#     impl = {}
#     try:
#         from src.Calculations.sma import compute_sma as my_sma  # your manual SMA
#         impl["sma"] = my_sma
#     except Exception:
#         impl["sma"] = None

#     try:
#         from src.Calculations.updown_runs import compute_updown_runs as my_runs  # your upgraded analyzer
#         impl["runs"] = my_runs
#     except Exception:
#         # fallback to legacy if available
#         try:
#             from src.Calculations.updown_runs import count_runs as legacy
#             impl["runs_legacy"] = legacy
#         except Exception:
#             impl["runs"] = None

#     try:
#         from src.Calculations.daily_returns import simple_returns as my_daily_returns
#         impl["daily_returns"] = my_daily_returns
#     except Exception:
#         impl["daily_returns"] = None

#     try:
#         from src.Calculations.max_profit import max_profit as my_max_profit
#         impl["max_profit"] = my_max_profit
#     except Exception:
#         impl["max_profit"] = None

#     return impl

# compare_with_my_impl = st.checkbox("Compare against my implementation (optional)", value=False)
# my_impl = try_import_my_impl() if compare_with_my_impl else {}

# # Access loaded data from Home
# if "data" not in st.session_state or st.session_state["data"] is None:
#     st.warning("Load a ticker & date range on the Home page first.")
#     st.stop()

# df_global = st.session_state["data"].copy()
# df_global["Date"] = pd.to_datetime(df_global["Date"])
# close_global = pd.to_numeric(df_global["Close"], errors="coerce")

# # 1) SMA VALIDATION
# st.header("1) Simple Moving Average (SMA)")

# st.write("**Reference method (independent):** O(1) **prefix-sum** SMA (not pandas `.rolling()`, not your function).")

# def sma_prefix_sum(series: pd.Series, window: int) -> pd.Series:
#     s = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
#     n = len(s)
#     out = np.full(n, np.nan, dtype=float)
#     # prefix sums with leading zero
#     pref = np.zeros(n + 1, dtype=float)
#     for i in range(n):
#         pref[i+1] = pref[i] + (0.0 if np.isnan(s[i]) else s[i])
#     count = np.zeros(n + 1, dtype=int)
#     for i in range(n):
#         count[i+1] = count[i] + (0 if np.isnan(s[i]) else 1)
#     for i in range(window-1, n):
#         total = pref[i+1] - pref[i+1-window]
#         cnt = count[i+1] - count[i+1-window]
#         out[i] = np.nan if cnt < window else total / window
#     return pd.Series(out, index=series.index, name=f"SMA{window}")

# # Build at least 5 test cases
# sma_tests = [
#     {"name": "Ascending 1..10, w=3", "series": pd.Series(range(1, 11)), "w": 3},
#     {"name": "Shorter than window, w=5", "series": pd.Series([10, 20, 30, 40]), "w": 5},
#     {"name": "With NaNs inside, w=3", "series": pd.Series([10, np.nan, 30, 40, 50]), "w": 3},
#     {"name": "Constant series, w=4", "series": pd.Series([7, 7, 7, 7, 7, 7]), "w": 4},
#     {"name": "Real data slice (first 20)", "series": close_global.head(20).reset_index(drop=True), "w": 5},
# ]

# sma_rows = []
# for t in sma_tests:
#     ref = sma_prefix_sum(t["series"], t["w"])
#     # trusted baseline for cross-check only (not required, but informative)
#     pandas_ref = t["series"].rolling(t["w"]).mean()
#     ok_vs_pandas = bool(np.allclose(ref.fillna(np.nan), pandas_ref.fillna(np.nan), equal_nan=True))

#     row = {"case": t["name"], "window": t["w"], "ref_matches_pandas": ok_vs_pandas}

#     if compare_with_my_impl and my_impl.get("sma"):
#         mine = my_impl["sma"](t["series"], t["w"])
#         ok_vs_mine = bool(np.allclose(ref.fillna(np.nan), mine.fillna(np.nan), equal_nan=True))
#         row["my_impl_agrees"] = ok_vs_mine

#     sma_rows.append(row)

# st.dataframe(pd.DataFrame(sma_rows), use_container_width=True)

# # 2) UP/DOWN RUNS VALIDATION
# st.header("2) Upward & Downward Runs")

# st.write("**Reference method (independent):** vectorized **sign-of-diff + run-length** grouping.")

# def runs_reference(df: pd.DataFrame):
#     d = df.copy()
#     d["Date"] = pd.to_datetime(d["Date"])
#     c = pd.to_numeric(d["Close"], errors="coerce")
#     diff = c.diff()                   # NaN at first row
#     sign = diff.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
#     # run id increments when sign changes or zero
#     run_id = (sign != sign.shift(1)).cumsum()
#     out = []
#     for rid, grp in d.assign(sign=sign).groupby(run_id):
#         s = grp["sign"].iloc[0]
#         if s == 0:   # flat streaks break runs, ignore
#             continue
#         out.append({
#             "type": "up" if s == 1 else "down",
#             "len": len(grp),  # includes both endpoints
#             "start": grp["Date"].iloc[0],
#             "end": grp["Date"].iloc[-1],
#             "start_idx": grp.index[0],
#             "end_idx": grp.index[-1],
#         })
#     runs_df = pd.DataFrame(out)
#     if runs_df.empty:
#         summary = dict(up_runs_count=0, down_runs_count=0, up_days_total=0, down_days_total=0,
#                        longest_up={"len":0,"start":None,"end":None,"start_idx":None,"end_idx":None},
#                        longest_down={"len":0,"start":None,"end":None,"start_idx":None,"end_idx":None})
#         return summary, runs_df
#     up = runs_df[runs_df.type=="up"]
#     down = runs_df[runs_df.type=="down"]
#     longest_up = up.loc[up["len"].idxmax()].to_dict() if not up.empty else {"len":0,"start":None,"end":None,"start_idx":None,"end_idx":None}
#     longest_down = down.loc[down["len"].idxmax()].to_dict() if not down.empty else {"len":0,"start":None,"end":None,"start_idx":None,"end_idx":None}
#     summary = dict(
#         up_runs_count=int(len(up)), down_runs_count=int(len(down)),
#         up_days_total=int(up["len"].sum()) if not up.empty else 0,
#         down_days_total=int(down["len"].sum()) if not down.empty else 0,
#         longest_up={k:int(v) if "idx" in k else v for k,v in longest_up.items()},
#         longest_down={k:int(v) if "idx" in k else v for k,v in longest_down.items()},
#     )
#     return summary, runs_df

# # Five diverse test series
# runs_tests = [
#     {"name": "Strictly increasing", "series": [1,2,3,4,5,6]},
#     {"name": "Strictly decreasing", "series": [6,5,4,3,2,1]},
#     {"name": "Mixed with flats", "series": [1,1,2,3,3,2,1,1,2]},
#     {"name": "Single element", "series": [10]},
#     {"name": "Real data slice (first 40)", "series": close_global.head(40).tolist()},
# ]

# rows = []
# for t in runs_tests:
#     dtest = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=len(t["series"]), freq="D"),
#                           "Close": t["series"]})
#     ref_summary, ref_df = runs_reference(dtest)
#     row = {
#         "case": t["name"],
#         "ref_up_runs": ref_summary["up_runs_count"],
#         "ref_down_runs": ref_summary["down_runs_count"],
#         "ref_longest_up": ref_summary["longest_up"]["len"],
#         "ref_longest_down": ref_summary["longest_down"]["len"],
#     }
#     if compare_with_my_impl and my_impl.get("runs"):
#         mine = my_impl["runs"](dtest)
#         row["my_up_runs"] = mine["up_runs_count"]
#         row["my_down_runs"] = mine["down_runs_count"]
#         row["agree_counts"] = (row["ref_up_runs"]==row.get("my_up_runs")) and (row["ref_down_runs"]==row.get("my_down_runs"))
#         row["agree_longest"] = (row["ref_longest_up"]==mine["longest_up"]["len"]) and (row["ref_longest_down"]==mine["longest_down"]["len"])
#     rows.append(row)

# st.dataframe(pd.DataFrame(rows), use_container_width=True)

# # 3) DAILY RETURNS VALIDATION
# st.header("3) Daily Returns rₜ = (Pₜ − Pₜ₋₁) / Pₜ₋₁")

# st.write("**Reference method (independent):** direct vectorized formula; cross-check with `pct_change()`.")

# def returns_reference(close: pd.Series) -> pd.Series:
#     c = pd.to_numeric(close, errors="coerce")
#     return (c - c.shift(1)) / c.shift(1)

# ret_ref = returns_reference(close_global)
# ret_pct = close_global.pct_change()
# matches_pct = bool(np.allclose(ret_ref.fillna(np.nan), ret_pct.fillna(np.nan), equal_nan=True))

# row = {"series": "Loaded data", "ref_vs_pct_change": matches_pct}
# if compare_with_my_impl and my_impl.get("daily_returns"):
#     mine = my_impl["daily_returns"](close_global)
#     row["my_impl_agrees"] = bool(np.allclose(ret_ref.fillna(np.nan), mine.fillna(np.nan), equal_nan=True))

# st.dataframe(pd.DataFrame([row]), use_container_width=True)

# # Add 4 more synthetic checks
# more_cases = [
#     pd.Series([100, 110, 121, 133.1]),                     # compounding 10%
#     pd.Series([100, 90, 81, 72.9]),                        # -10%
#     pd.Series([100, np.nan, 105, 115]),                    # NaN gap
#     pd.Series([50, 50, 50, 50])                            # flat
# ]
# rows = []
# for i, s in enumerate(more_cases, 1):
#     ref = returns_reference(s)
#     pct = s.pct_change()
#     rows.append({"case": f"synthetic #{i}", "ref_vs_pct_change": bool(np.allclose(ref.fillna(np.nan), pct.fillna(np.nan), equal_nan=True))})
# st.dataframe(pd.DataFrame(rows), use_container_width=True)

# # 4) MAX PROFIT (LeetCode 122) VALIDATION
# st.header("4) Max Profit — Multiple Transactions (LeetCode 122)")

# st.write("**Reference method (independent):** two-state **Dynamic Programming** (hold/cash), "
#          "which is equivalent to the greedy sum of positive differences.")

# def max_profit_dp(prices: list[float]) -> float:
#     if not prices:
#         return 0.0
#     hold = -float("inf")
#     cash = 0.0
#     for p in prices:
#         hold = max(hold, cash - p)
#         cash = max(cash, hold + p)
#     return cash

# mp_tests = [
#     {"name": "Increasing only", "prices": [1,2,3,4,5]},
#     {"name": "Decreasing only", "prices": [5,4,3,2,1]},
#     {"name": "Valley→Peak→Valley", "prices": [7,1,5,3,6,4]},
#     {"name": "Small random", "prices": [3,2,6,5,0,3]},
#     {"name": "Real data slice (first 30 closes)", "prices": close_global.head(30).dropna().tolist()},
# ]

# mp_rows = []
# for t in mp_tests:
#     ref = max_profit_dp(t["prices"])
#     row = {"case": t["name"], "ref_profit": round(ref, 6)}
#     if compare_with_my_impl and my_impl.get("max_profit"):
#         mine = my_impl["max_profit"](t["prices"])
#         row["my_profit"] = round(float(mine), 6)
#         row["agree"] = abs(row["ref_profit"] - row["my_profit"]) < 1e-9
#     mp_rows.append(row)

# st.dataframe(pd.DataFrame(mp_rows), use_container_width=True)

# # Summary badges
# st.subheader("Summary")
# summary_notes = []
# if compare_with_my_impl:
#     # simple aggregate view
#     all_ok = True
#     # (We already computed agreement row-by-row; we can just remind user to scroll.)
#     summary_notes.append("Comparison against your implementations is shown in the tables above.")
# else:
#     summary_notes.append("Only reference computations were run (your functions were **not** called). "
#                          "Enable the toggle above if you want pass/fail vs. your implementation.")
# st.info(" • ".join(summary_notes))
