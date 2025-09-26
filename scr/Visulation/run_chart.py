# src/Visualization/run_chart.py
import matplotlib.pyplot as plt
import pandas as pd

def plot_runs(df: pd.DataFrame, highlight: dict | None = None):
    """
    Plot Close segmented into up (green) and down (orange) runs.
    If `highlight` is given (dict with 'start_idx','end_idx'), that segment
    is drawn thicker on top.
    """
    dates = pd.to_datetime(df["Date"])
    prices = df["Close"].values

    fig, ax = plt.subplots(figsize=(10, 5))

    i = 0
    while i < len(prices) - 1:
        j = i + 1
        if prices[j] >= prices[i]:  # up run
            while j < len(prices) and prices[j] >= prices[j-1]:
                j += 1
            ax.plot(dates[i:j], prices[i:j], color="green", label="Up runs" if i == 0 else "")
        else:  # down run
            while j < len(prices) and prices[j] <= prices[j-1]:
                j += 1
            ax.plot(dates[i:j], prices[i:j], color="orange", label="Down runs" if i == 0 else "")
        i = j - 1

    # optional highlight (e.g., longest streak)
    if highlight and all(k in highlight for k in ("start_idx","end_idx")):
        si, ei = int(highlight["start_idx"]), int(highlight["end_idx"])
        si = max(si, 0); ei = min(ei, len(prices)-1)
        if ei > si:
            ax.plot(dates[si:ei+1], prices[si:ei+1], linewidth=3)

    ax.set_title("Upward and Downward Runs (Close)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    return fig
