# ./fin_agent/tools/stock_tools.py
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from langchain.tools import tool
from io import StringIO
import datetime

@tool
def get_stock_data(ticker: str, start_date: str, end_date: str) -> str:
    """Get daily stock price data for a U.S. company using its ticker."""
    try:
        stock = yf.Ticker(ticker.upper())
        df = stock.history(start=start_date, end=end_date, interval="1d")
        if df.empty:
            return f"No price data found for ticker {ticker} in the given date range."
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df.rename(columns={'Date': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
        return df[['time', 'open', 'high', 'low', 'close', 'volume']].to_csv(index=False)
    except Exception as e:
        return f"Error getting stock data: {e}"

@tool
def calculate_technical_indicators(csv_data: str) -> str:
    """
    (Data is provided automatically) Calculate technical indicators (RSI, MACD, SMA).
    """
    try:
        df = pd.read_csv(StringIO(csv_data))
        if 'close' not in df.columns:
            return "Invalid CSV data. 'close' column is missing."
        df.ta.rsi(close='close', append=True, length=14)
        df.ta.macd(close='close', append=True, fast=12, slow=26, signal=9)
        df.ta.sma(close='close', append=True, length=50)
        indicator_cols = ['RSI_14', 'MACD_12_26_9', 'SMA_50']
        if not all(col in df.columns for col in indicator_cols):
             return "Could not calculate all technical indicators."
        latest = df.iloc[-1][indicator_cols]
        return f"Latest technical indicators:\n{latest.to_string()}"
    except Exception as e:
        return f"Error calculating technical indicators: {e}"