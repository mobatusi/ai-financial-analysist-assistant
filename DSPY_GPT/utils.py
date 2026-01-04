import yfinance as yf
import json
import pandas as pd
from pandas import Timestamp  

# ---------------------------------------------------------------------
# Task 3: Create Utility Functions to Fetch, Analyze, and Format Stock Market Data
# ---------------------------------------------------------------------

def get_stock_data(ticker):
    """
    Fetches financial information for a given stock symbol using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Latest price and metrics
        price = info.get('currentPrice', 0.0)
        pct_change = info.get('regularMarketChangePercent', 0.0)
        name = info.get('longName', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        beta = info.get('beta', 'N/A')
        sector = info.get('sector', 'N/A')
        
        # 30-day historical data
        history = stock.history(period="1mo")
        # Reset index to include Date as a column before converting to JSON
        history_json = history.reset_index().to_json(date_format='iso', orient='records')
        
        return {
            'price': price,
            'pct_change': pct_change,
            'name': name,
            'pe_ratio': pe_ratio,
            'beta': beta,
            'sector': sector,
            'history': history_json
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return {
            'price': 0.0,
            'pct_change': 0.0,
            'name': 'Error',
            'pe_ratio': 'N/A',
            'beta': 'N/A',
            'sector': 'N/A',
            'history': '[]'
        }

def history_to_dataframe(history_json):
    """
    Converts the stock history data (in JSON format) into a pandas DataFrame.
    """
    try:
        data = json.loads(history_json)
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Ensure proper handling of date columns
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            elif 'index' in df.columns: # Sometimes yfinance returns 'index' instead of 'Date' after reset_index
                df['index'] = pd.to_datetime(df['index'])
                df.set_index('index', inplace=True)
                df.index.name = 'Date'
            
            # Sort data chronologically
            df.sort_index(inplace=True)
            
        return df
    except Exception as e:
        print(f"Error converting history to dataframe: {e}")
        return pd.DataFrame()
