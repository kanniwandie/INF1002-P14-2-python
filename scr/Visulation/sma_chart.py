import matplotlib.pyplot as plt

def plot_close_vs_sma(df, sma_series):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Date"], df["Close"], label="Close Price")
    ax.plot(df["Date"], sma_series, label="SMA")
    ax.set_title("Close Price vs SMA")
    ax.legend()
    return fig
