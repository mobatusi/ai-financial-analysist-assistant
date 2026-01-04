from DSPY_GPT.utils import get_stock_data, history_to_dataframe
import pandas as pd

def test_utils():
    ticker = "AAPL"
    print(f"Fetching data for {ticker}...")
    data = get_stock_data(ticker)
    
    # Check keys
    expected_keys = ['price', 'pct_change', 'name', 'pe_ratio', 'beta', 'sector', 'history']
    for key in expected_keys:
        if key not in data:
            print(f"FAILED: Key '{key}' not found in output dictionary.")
            return

    print("SUCCESS: All keys found.")
    print(f"Name: {data['name']}")
    print(f"Price: {data['price']}")
    print(f"Sector: {data['sector']}")
    
    # Check history
    print("Testing history_to_dataframe...")
    df = history_to_dataframe(data['history'])
    if isinstance(df, pd.DataFrame) and not df.empty:
        print("SUCCESS: DataFrame created and is not empty.")
        print(f"DataFrame columns: {df.columns.tolist()}")
        print(f"DataFrame index name: {df.index.name}")
        print("First 5 rows of history:")
        print(df.head())
    else:
        print("FAILED: History conversion to DataFrame failed or returned empty.")

if __name__ == "__main__":
    test_utils()
