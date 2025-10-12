How to Run the Project
Requirements

Python 3.9 or higher

Internet connection (needed for Yahoo Finance data)

Basic Python tools: pip (comes with Python)

1. Install Python Packages
------------------------------------
First, install the required packages

If you don’t have it yet, just install the core libraries manually:

```python 
pip install streamlit
pip install yfinance
pip install matplotlib
pip install numpy
pip install pandas
```


What these do:
- streamlit → for the web app
- yfinance → to fetch stock data
- matplotlib → creating static, animated, and interactive visualizations
- numpy → math operations
- pandas → data handling


2. Run the App
-------------------------------------
```python
streamlit run main.py
```


This will start a local server.
Look for a link like:

http://localhost:8501

Click it (or paste into a browser) — the dashboard will open. 
