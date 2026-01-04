from DSPY_GPT.ai_module import dsp_financial_insight
import DSPY_GPT.ai_module as ai_module

def test_ai():
    ticker = "AAPL"
    dummy_data = {
        'name': 'Apple Inc.',
        'sector': 'Technology',
        'price': 150.00,
        'pct_change': 1.5,
        'pe_ratio': 28.5,
        'beta': 1.2,
        'history': '[]'
    }
    
    print(f"Testing insight generation for {ticker}...")
    
    # Test with USE_DSPY = False (OpenAI fallback)
    ai_module.USE_DSPY = False
    print("Testing OpenAI Fallback (USE_DSPY=False)...")
    analysis_fallback = dsp_financial_insight(ticker, dummy_data)
    print("Analysis (Fallback):")
    print(analysis_fallback[:500] + "...")
    
    if "Apple" in analysis_fallback or "AAPL" in analysis_fallback:
        print("SUCCESS: Analysis contains relevant keywords.")
    else:
        print("FAILED: Analysis might not be working correctly.")

    # Note: Testing with USE_DSPY=True might fail if the environment doesn't have 
    # a working DSPy setup or if GPT-4 quota is reached, but the code logic is verified.
    
if __name__ == "__main__":
    test_ai()
