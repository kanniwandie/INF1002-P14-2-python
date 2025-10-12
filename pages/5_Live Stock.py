# pages/5_Live_Stock.py

"""
Streamlit Page: Maximum Profit Calculation (Live Dashboard)

This page provides a live stock dashboard powered by Yahoo Finance. 
It displays real-time price updates every 5 seconds, supports multiple 
historical ranges (1D–All), and includes a Plotly chart alongside 
snapshot metrics such as market cap, EPS, and P/E ratio.
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# Page setup and header
# -----------------------------
st.set_page_config(page_title="📊 Live Stock Dashboard", layout="wide")
st.title("📊 Live Stock Dashboard")
st.caption("Real-time market snapshot powered by Yahoo Finance.")

# -----------------------------
# Sidebar controls (user inputs)
# -----------------------------
with st.sidebar:
    st.header("Inputs")

    # Popular tickers (label → symbol)
    POPULAR = [
        ("Apple", "AAPL"),
        ("Microsoft", "MSFT"),
        ("NVIDIA", "NVDA"),
        ("Amazon", "AMZN"),
        ("Alphabet (Google)", "GOOGL"),
        ("Meta", "META"),
        ("Tesla", "TSLA"),
        ("S&P 500", "^GSPC"),
    ]

    # Preload session ticker if available; default = AAPL
    session_ticker = (
        st.session_state.get("cfg", {}).get("ticker")
        or st.session_state.get("maxprofit_meta", {}).get("ticker")
    )
    default_ticker = (session_ticker or "AAPL").upper()

    # Map labels ↔ symbols for dropdown selection
    symbol_lookup = {label: sym for label, sym in POPULAR}
    reverse_lookup = {sym: label for label, sym in POPULAR}
    default_label = reverse_lookup.get(default_ticker, "Custom…")

    # Dropdown with “Custom…” option
    labels = [label for label, _ in POPULAR] + ["Custom…"]
    default_index = labels.index(default_label) if default_label in labels else labels.index("Custom…")
    label_choice = st.selectbox("Popular tickers", labels, index=default_index)

    # Custom ticker text input (overrides dropdown if filled)
    custom_prefill = "" if default_label != "Custom…" else default_ticker
    custom_ticker = st.text_input(
        "Or enter a custom ticker",
        value=custom_prefill,
        placeholder="e.g., IBM or ^GSPC"
    ).strip().upper()

    # Final ticker resolution (custom > dropdown > default)
    dropdown_symbol = symbol_lookup.get(label_choice)
    ticker = (custom_ticker or dropdown_symbol or default_ticker).upper()

    # Time range selection
    ranges = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "All"]
    sel_range = st.radio("Range", ranges, index=0, horizontal=True, label_visibility="visible")

# -----------------------------
# Auto-refresh setup (5 seconds)
# -----------------------------
st_autorefresh(interval=5_000, key="live_refresh_every_5s")
st.caption("⏳ Auto-refresh: every **5s**")

# -----------------------------
# Helper: Convert range → yfinance args
# -----------------------------
def range_to_history_args(rng: str):
    """
    Translate a range label into yfinance.history() parameters.

    Args:
        rng (str): Range from the UI (e.g., '1D', '1M', 'YTD', 'All').

    Returns:
        dict: Parameters for yf.Ticker().history() with period/start and interval.
    """
    if rng == "1D":
        return dict(period="1d", interval="1m")  # 1-min intraday data
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
    return dict(period="max", interval="1wk")  # Default: full range

# -----------------------------
# Helper: Fetch snapshot + history
# -----------------------------
@st.cache_data(ttl=4)
def fetch_snapshot_and_history(ticker: str, rng: str):
    """
    Fetch live snapshot and historical price data for a given ticker.

    Args:
        ticker (str): Stock symbol (e.g., 'AAPL').
        rng (str): Selected range label (controls period/interval).

    Returns:
        tuple[dict, pd.DataFrame]:
            info (dict): Snapshot fields (fast_info + info).
            df (pd.DataFrame): Historical prices with columns ['Date','Close'].
    """
    stock = yf.Ticker(ticker)
    info = stock.fast_info if hasattr(stock, "fast_info") else {}

    # Fallback to .info for missing fields
    try:
        info_full = stock.info
        info = {**info_full, **info}
    except Exception:
        pass

    # Retrieve price history
    args = range_to_history_args(rng)
    df = stock.history(**args)
    if not df.empty:
        df = df.reset_index().rename(columns={"Datetime": "Date"})
        if "Date" not in df.columns:
            df["Date"] = df.index
        df["Date"] = pd.to_datetime(df["Date"])
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    return info, df

# -----------------------------
# Fetch data and handle missing cases
# -----------------------------
info, df = fetch_snapshot_and_history(ticker, sel_range)
if df is None or df.empty:
    st.error("No data returned. Try a different range or ticker.")
    st.stop()

# -----------------------------
# Layout: Chart (left) + Snapshot (right)
# -----------------------------
left, right = st.columns([2, 1])

# --- Left: Plot chart ---
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

        # Add small y-padding for visual clarity
        y_min, y_max = float(y.min()), float(y.max())
        pad = max((y_max - y_min) * 0.06, 0.5)
        y_range = [y_min - pad, y_max + pad]

        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        last_price = (
            info.get("last_price") or 
            info.get("regularMarketPrice") or 
            (y[-1] if len(y) else None)
        )

        fig = go.Figure()

        # Add price line
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            line=dict(width=2.5, color="#1f77b4"),
            name="Close"
        ))

        # Reference lines for last and previous close
        if isinstance(last_price, (int, float)):
            fig.add_hline(y=last_price, line_dash="dot", line_color="blue", opacity=0.6)
        if isinstance(prev_close, (int, float)):
            fig.add_hline(y=prev_close, line_dash="dash", line_color="gray", opacity=0.4)

        # Minimal clean layout
        fig.update_layout(
            template="plotly_white",
            height=420,
            margin=dict(l=20, r=20, t=10, b=20),
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=True, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=True, zeroline=False, range=y_range),
        )

        st.plotly_chart(fig, use_container_width=True)

# --- Right: Snapshot section ---
with right:
    st.subheader("Snapshot")

    # Key live data fields
    price = info.get("last_price") or info.get("regularMarketPrice")
    delta = info.get("regularMarketChange", None)
    pct   = info.get("regularMarketChangePercent", None)

    # Format primary metric
    price_str = f"{price:.2f}" if isinstance(price, (int, float)) else "—"
    delta_str = (
        f"{delta:+.2f} ({pct:+.2f}%)"
        if isinstance(delta, (int, float)) and isinstance(pct, (int, float))
        else (f"{delta:+.2f}" if isinstance(delta, (int, float)) else None)
    )

    st.metric(f"{ticker} Price", price_str, delta=delta_str)

    # Secondary snapshot values
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
        """
        Format numeric or text values for display.

        Args:
            x: Value to format (numeric or object).
            digits (int): Decimal precision for floats.

        Returns:
            str: Formatted value or "—" if missing.
        """
        return "—" if x is None or (isinstance(x, float) and pd.isna(x)) else (
            f"{x:.{digits}f}" if isinstance(x, (int, float)) else x
        )

    # Display key market metrics
    st.write("**At close:**", fmt(prev_close))
    st.write("**Open:**", fmt(open_px))
    st.write("**Day's range:**", f"{fmt(day_low)} – {fmt(day_high)}")
    st.write("**52-week range:**", f"{fmt(wk52_low)} – {fmt(wk52_high)}")
    st.write("**Volume:**", fmt(vol, 0))
    st.write("**Market Cap:**", fmt(mktcap, 0))
    st.write("**P/E (TTM):**", fmt(pe_ttm))
    st.write("**EPS (TTM):**", fmt(eps_ttm))
    st.write("**Forward Dividend & Yield:**", f"{fmt(div_yield*100 if isinstance(div_yield,(int,float)) else div_yield)}%")

# -----------------------------
# Footer
# -----------------------------
st.caption(
    f"Range: **{sel_range}** • Data source: yfinance • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
