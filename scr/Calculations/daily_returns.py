import csv
from scr.data.yfinance_client import fetch_prices

def dr_calc(df, index):
    dc = float(df["Close"][index])
    pc = float(df["Close"][index-1])
    daily_return = ((dc-pc)/pc)*100
    return daily_return