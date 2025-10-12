# INF1002 P14_2

How to Run the Project

Requirements:

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

3. Project Structure
-------------------------------------
```Python
Project/
├── .vscode/
│   ├── launch.json
│   ├── settings.json
├── pages/
│   ├── 1_Simple Moving Average.py
│   ├── 2_Upward and Downward Runs.py      
│   ├── 3_Daily Returns.py    
│   ├── 4_Maximum Profit Calculation.py         
│   └── 5_Live Stock.py     
├── scr/
│   ├── Calculations/
│   │   ├── __init__.py
│   │   ├── daily_returns.py
│   │   ├── lc121_single.py
│   │   ├── lc714_fee.py
│   │   ├── max_profit.py
│   │   ├── sma.py
│   │   ├── trade_utils.py
│   │   └── updown_runs.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_processing.py
│   │   ├── data.py
│   │   └── yfinance_client.py         
│   ├── Visualization/
│   │   ├── sma_chart.py
│   │   └── updown_chart.py
├── .gitignore                     
└── Starting_page.py       
```     