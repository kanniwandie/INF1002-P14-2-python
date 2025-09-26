import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="📊 Live Stock Dashboard", layout="wide")

st.title("📊 Live Stock Dashboard")
st.caption("Real-time market snapshot powered by Yahoo Finance.")

# Controls (left sidebar)
with st.sidebar:
    st.header("Inputs")
    ticker = st.text_input("Ticker", value="AAPL").strip().upper()

    # Yahoo-style ranges
    ranges = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "All"]
    sel_range = st.radio("Range", ranges, index=0, horizontal=True, label_visibility="visible")

# Hard-code auto-refresh every 5 seconds
st_autorefresh(interval=5_000, key="live_refresh_every_5s")
st.caption("⏳ Auto-refresh: every **5s**")

# Data fetch helpers
def range_to_history_args(rng: str):
    """
    Map UI range to yfinance .history(...) arguments.
    Prefer intervals that keep the number of points reasonable and intraday
    granularity where appropriate.
    """
    if rng == "1D":
        return dict(period="1d", interval="1m")    # intraday 1-minute
    if rng == "5D":
        return dict(period="5d", interval="5m")
    if rng == "1M":
        return dict(period="1mo", interval="30m")
    if rng == "6M":
        return dict(period="6mo", interval="1d")
    if rng == "YTD":
        start = datetime(datetime.now().year, 1, 1)
        return dict(start=start, interval="1d")
    if rng == "1Y":
        return dict(period="1y", interval="1d")
    if rng == "5Y":
        return dict(period="5y", interval="1wk")
    # All available history (max)
    return dict(period="max", interval="1wk")

@st.cache_data(ttl=4)  # re-use for 4s between the 5s refreshes
def fetch_snapshot_and_history(ticker: str, rng: str):
    stock = yf.Ticker(ticker)
    info = stock.fast_info if hasattr(stock, "fast_info") else {}
    # fall back to .info for fields fast_info may not provide
    try:
        info_full = stock.info
        info = {**info_full, **info}
    except Exception:
        pass

    args = range_to_history_args(rng)
    df = stock.history(**args)
    if not df.empty:
        df = df.reset_index().rename(columns={"Datetime": "Date"})
        # ensure we always have "Date" and "Close"
        if "Date" not in df.columns:
            # sometimes index is already a datetime index named something else
            df["Date"] = df.index
        df["Date"] = pd.to_datetime(df["Date"])
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    return info, df

# Fetch & guard
info, df = fetch_snapshot_and_history(ticker, sel_range)
if df is None or df.empty:
    st.error("No data returned. Try a different range or ticker.")
    st.stop()

# Layout: Chart (left) + Snapshot (right)
left, right = st.columns([2, 1])

with left:
    title = f"{ticker} Price — {sel_range}"
    st.subheader(title)

    chart_df = df[["Date", "Close"]].copy()
    chart_df["Date"] = pd.to_datetime(chart_df["Date"])
    chart_df = chart_df.dropna().sort_values("Date")

    if chart_df.empty:
        st.info("No chart data available for this range.")
    else:
        y = chart_df["Close"].values
        x = chart_df["Date"].values

        # Padding for visibility
        y_min, y_max = float(y.min()), float(y.max())
        pad = max((y_max - y_min) * 0.06, 0.5)
        y_range = [y_min - pad, y_max + pad]

        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        last_price = (info.get("last_price") or info.get("regularMarketPrice") or (y[-1] if len(y) else None))

        fig = go.Figure()

        # Simple clean line chart
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            line=dict(width=2.5, color="#1f77b4"),
            name="Close"
        ))

        # Reference lines
        if isinstance(last_price, (int, float)):
            fig.add_hline(y=last_price, line_dash="dot", line_color="blue", opacity=0.6)

        if isinstance(prev_close, (int, float)):
            fig.add_hline(y=prev_close, line_dash="dash", line_color="gray", opacity=0.4)

        # Minimal layout (no grid, no axis titles)
        fig.update_layout(
            template="plotly_white",
            height=420,
            margin=dict(l=20, r=20, t=10, b=20),
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=True, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=True, zeroline=False, range=y_range),
        )

        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Snapshot")
    # Try to read live-ish fields defensively
    price = info.get("last_price") or info.get("regularMarketPrice")
    delta = info.get("regularMarketChange", None)
    pct   = info.get("regularMarketChangePercent", None)

    if isinstance(price, (int, float)):
        price_str = f"{price:.2f}"
    else:
        price_str = "—"

    delta_str = None
    if isinstance(delta, (int, float)) and isinstance(pct, (int, float)):
        delta_str = f"{delta:+.2f} ({pct:+.2f}%)"
    elif isinstance(delta, (int, float)):
        delta_str = f"{delta:+.2f}"

    st.metric(f"{ticker} Price", price_str, delta=delta_str)

    # Secondary fields (best-effort, may vary by ticker)
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    open_px    = info.get("open") or info.get("regularMarketOpen")
    day_low    = info.get("dayLow")
    day_high   = info.get("dayHigh")
    wk52_low   = info.get("fiftyTwoWeekLow")
    wk52_high  = info.get("fiftyTwoWeekHigh")
    vol        = info.get("volume")
    mktcap     = info.get("marketCap")
    pe_ttm     = info.get("trailingPE")
    eps_ttm    = info.get("trailingEps")
    div_yield  = info.get("dividendYield")  

    def fmt(x, digits=2):
        return "—" if x is None or (isinstance(x, float) and pd.isna(x)) else (f"{x:.{digits}f}" if isinstance(x, (int,float)) else x)

    st.write("**At close:**", fmt(prev_close))
    st.write("**Open:**", fmt(open_px))
    st.write("**Day's range:**", f"{fmt(day_low)} – {fmt(day_high)}")
    st.write("**52-week range:**", f"{fmt(wk52_low)} – {fmt(wk52_high)}")
    st.write("**Volume:**", fmt(vol, 0))
    st.write("**Market Cap:**", fmt(mktcap, 0))
    st.write("**P/E (TTM):**", fmt(pe_ttm))
    st.write("**EPS (TTM):**", fmt(eps_ttm))
    st.write("**Forward Dividend & Yield:**", f"{fmt(div_yield*100 if isinstance(div_yield,(int,float)) else div_yield)}%")

# footer
st.caption(f"Range: **{sel_range}** • Data source: yfinance • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
