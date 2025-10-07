# scr/Visualization/sma_chart.py
"""
Visualization: Close vs. Simple Moving Average (SMA)

Creates a Matplotlib figure comparing the Close price time series against a
precomputed SMA series for the same dates.

"""

import matplotlib.pyplot as plt

def plot_close_vs_sma(df, sma_series):
    """
    Plot Close prices and a corresponding SMA series on the same axes.

    Args:
        df (pd.DataFrame): DataFrame containing at least columns:
            - "Date": datetime-like values
            - "Close": numeric close prices
        sma_series (pd.Series or array-like): Simple Moving Average values
            aligned to df["Date"] (same length/index alignment expected).

    Returns:
        matplotlib.figure.Figure: The generated figure object.

    Notes:
        - Assumes df["Date"] and sma_series are aligned (same order/length).
        - The function does not modify the input DataFrame or the SMA series.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Date"], df["Close"], label="Close Price")
    ax.plot(df["Date"], sma_series, label="SMA")
    ax.set_title("Close Price vs SMA")
    ax.legend()
    return fig
