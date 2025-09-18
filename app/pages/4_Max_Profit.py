# app/pages/4_Max_Profit.py
import streamlit as st
from datetime import date
from pathlib import Path
import pandas as pd
import os, sys

# allow `from src...` imports when running from /app
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

st.set_page_config(page_title="Max Profit (≤2 transactions)", page_icon="📈", layout="wide")
st.title("📈 Max Profit — Best Time to Buy and Sell Stock III (≤ 2 transactions)")

# imports
try:
    from src.data.yfinance_client import fetch_prices
    from src.Calculations.max_profit import max_profit_with_trades
    st.caption("Imports OK ✅")
except Exception as e:
    st.error("Import error ❌ — check folder/package names.")
    st.exception(e)
    st.stop()

# controls
with st.form("controls", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.4])
    with c1:
        ticker = st.text_input("Ticker", value="AAPL").strip().upper()
    with c2:
        start = st.date_input("Start date", value=date(2023, 1, 1))
    with c3:
        end = st.date_input("End date", value=date.today())
    with c4:
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
    run = st.form_submit_button("Compute Max Profit")

# action
if run:
    try:
        @st.cache_data(show_spinner=False)
        def _cached_fetch(t, s, e, i):
            return fetch_prices(t, s, e, i)

        df = _cached_fetch(ticker, str(start), str(end), interval)

        if df.empty or "Close" not in df.columns:
            st.warning("No price data available to compute profit.")
            st.stop()  # IMPORTANT: indented under the if

        # compute profit + trades (≤ 2)
        total_profit, trades = max_profit_with_trades(df, price_col="Close", date_col="Date")
        st.success(f"Maximum Profit (≤ 2 transactions): **${total_profit:.2f}**")

        if trades:
            rows = []
            for i, t in enumerate(trades, 1):
                rows.append({
                    "Trade": i,
                    "Buy date":  pd.to_datetime(t["buy_date"]).date(),
                    "Buy price": f"${t['buy_price']:.2f}",
                    "Sell date": pd.to_datetime(t["sell_date"]).date(),
                    "Sell price": f"${t['sell_price']:.2f}",
                    "Profit":    f"${t['profit']:.2f}",
                })
            st.subheader("Best times to buy & sell")
            st.table(pd.DataFrame(rows))
        else:
            st.info("No profitable trades in this period.")

        # preview + save
        with st.expander("Preview downloaded data", expanded=False):
            st.dataframe(df.tail(15), use_container_width=True)

        storage_dir = Path("storage/max_profit")
        storage_dir.mkdir(parents=True, exist_ok=True)
        csv_path = storage_dir / f"{ticker}_{start}_to_{end}_{interval}.csv"
        df.to_csv(csv_path, index=False)

        summary = pd.DataFrame([{
            "ticker": ticker, "start": str(start), "end": str(end),
            "interval": interval, "max_profit_2tx": total_profit
        }])
        summary_path = storage_dir / f"{ticker}_{start}_to_{end}_{interval}_summary.csv"
        summary.to_csv(summary_path, index=False)
        st.caption(f"Saved: `{csv_path.name}`, `{summary_path.name}` in storage/max_profit/")

    except Exception as e:
        st.error("Computation error")
        st.exception(e)
