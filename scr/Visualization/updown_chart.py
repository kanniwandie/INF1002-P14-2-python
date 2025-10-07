# scr/visulation/updown_chart.py
"""
Visualization: Upward & Downward Runs (Matplotlib)

Plots a Close-price time series segmented into upward (green) and downward
(orange) runs, with optional highlighting of a specific streak (e.g., the
longest up/down run) and optional boundary markers. Intended to work with
the `clean_df` returned by `compute_updown_runs()`.

"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def _prep(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a clean ['Date','Close'] frame, sorted by Date.

    Steps:
      - Coerce 'Date' to datetime and 'Close' to numeric.
      - Drop rows with missing Date/Close.
      - Sort by Date and reset index.

    Args:
        df (pd.DataFrame): Source with at least 'Date' and 'Close'.

    Returns:
        pd.DataFrame: Two-column DataFrame ['Date','Close'] ready for plotting.
    """
    d = df.copy()
    d["Date"]  = pd.to_datetime(d["Date"], errors="coerce")
    d["Close"] = pd.to_numeric(d["Close"], errors="coerce")
    d = d.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)
    return d[["Date", "Close"]]

def _resolve_indices(d: pd.DataFrame, highlight: dict | None):
    """
    Resolve start/end indices from highlight dict (supports idx or dates).

    The highlight mapping may include either:
      - {'start_idx': int, 'end_idx': int}, or
      - {'start': datetime-like, 'end': datetime-like}

    Args:
        d (pd.DataFrame): Cleaned DataFrame from `_prep` with ['Date','Close'].
        highlight (dict | None): Highlight spec (or None to disable).

    Returns:
        tuple[int | None, int | None]: (start_idx, end_idx) if resolvable,
        otherwise (None, None).
    """
    if not highlight:
        return None, None
    si = highlight.get("start_idx")
    ei = highlight.get("end_idx")
    if isinstance(si, int) and isinstance(ei, int):
        return si, ei

    # fall back to timestamps
    hs = pd.to_datetime(highlight.get("start"), errors="coerce")
    he = pd.to_datetime(highlight.get("end"), errors="coerce")
    if pd.notna(hs) and pd.notna(he):
        mask = (d["Date"] >= hs) & (d["Date"] <= he)
        idxs = np.where(mask.to_numpy())[0]
        if idxs.size >= 2:
            return int(idxs[0]), int(idxs[-1])
    return None, None

def plot_updown_runs(df: pd.DataFrame, highlight: dict | None = None, show_markers: bool = False):
    """
    Plot the Close series segmented into upward (green) and downward (orange) runs.
    Optionally highlight a specific streak (e.g., longest up/down) as a thicker line.

    Parameters
    ----------
    df : DataFrame with columns ["Date","Close"] (other cols ignored)
    highlight : dict|None
        Accepts either {'start_idx','end_idx',...} OR {'start','end',...}.
    show_markers : bool
        If True, draws small markers at run boundaries.

    Returns
    -------
    matplotlib.figure.Figure
    """
    d = _prep(df)
    dates = d["Date"].to_numpy()
    prices = d["Close"].to_numpy(dtype=float)
    n = len(d)
    fig, ax = plt.subplots(figsize=(10, 5))

    if n < 2:
        ax.plot(dates, prices)
        ax.set_title("Up/Down Runs (insufficient data)")
        return fig

    # segment-by-segment draw (green for up, orange for down)
    i = 0
    first_up_drawn = first_down_drawn = False
    while i < n - 1:
        j = i + 1
        if prices[j] >= prices[i]:  # upward
            while j < n and prices[j] >= prices[j-1]:
                j += 1
            ax.plot(
                dates[i:j], prices[i:j],
                color="green", linewidth=1.8,
                label="Up runs" if not first_up_drawn else None
            )
            first_up_drawn = True
        else:  # downward
            while j < n and prices[j] <= prices[j-1]:
                j += 1
            ax.plot(
                dates[i:j], prices[i:j],
                color="orange", linewidth=1.8,
                label="Down runs" if not first_down_drawn else None
            )
            first_down_drawn = True

        if show_markers:
            ax.scatter(dates[i], prices[i], s=18)
            ax.scatter(dates[j-1], prices[j-1], s=18)
        i = j - 1

    # optional highlight
    si, ei = _resolve_indices(d, highlight)
    if si is not None and ei is not None and ei > si:
        ax.plot(dates[si:ei+1], prices[si:ei+1], linewidth=3.4, color="black", alpha=0.8)

    ax.set_title("Upward & Downward Runs (Close)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig
