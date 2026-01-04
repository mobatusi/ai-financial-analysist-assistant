import os
import traceback
from typing import Dict
import dspy
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Prompt Template
INSIGHT_PROMPT_TEMPLATE = """
You are a helpful financial analyst. Given the ticker {ticker} and the following data,
produce a concise investment analysis (3–6 short paragraphs) covering:
- recent price action summary
- key fundamental metrics (PE, beta)
- risk considerations
- investment thesis and recommended time horizon

Raw data:
{raw_summary}
"""

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_DSPY = False

# Initialize DSPy model
try:
    lm = dspy.LM(model="openai/gpt-4", api_key=OPENAI_API_KEY)
    dspy.configure(lm=lm)
    USE_DSPY = True
except Exception:
    USE_DSPY = False

# Initialize OpenAI client (fallback option)
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception:
    client = None

# ---------------------------------------------------------------------
#  Task 4: Implement Financial Insight Generation using DSPy
# ---------------------------------------------------------------------

class FinancialInsight(dspy.Signature):
    """
    You are a helpful financial analyst. Produce a concise investment analysis (3–6 short paragraphs) 
    based on the provided ticker and raw stock data metrics.
    """
    ticker = dspy.InputField(desc="The stock symbol (e.g. AAPL)")
    raw_summary = dspy.InputField(desc="Structured summary of key company data")
    analysis = dspy.OutputField(desc="A concise investment analysis (3-6 short paragraphs)")

def dsp_financial_insight(ticker: str, stock_data: Dict) -> str:
    """
    Generates financial insights using DSPy or an OpenAI fallback.
    """
    # Format the raw summary string from stock_data
    raw_summary = (
        f"Company Name: {stock_data.get('name', 'N/A')}\n"
        f"Sector: {stock_data.get('sector', 'N/A')}\n"
        f"Current Price: ${stock_data.get('price', 0.0):.2f}\n"
        f"Change %: {stock_data.get('pct_change', 0.0):.2f}%\n"
        f"P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}\n"
        f"Beta: {stock_data.get('beta', 'N/A')}\n"
    )

    if USE_DSPY:
        try:
            predictor = dspy.Predict(FinancialInsight)
            result = predictor(ticker=ticker, raw_summary=raw_summary)
            return result.analysis
        except Exception as e:
            print(f"DSPy execution failed: {e}")
            # Fall through to OpenAI if label-based execution fails

    # Fallback to OpenAI API
    if client:
        try:
            prompt = INSIGHT_PROMPT_TEMPLATE.format(ticker=ticker, raw_summary=raw_summary)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI fallback failed: {e}")

    # Final heuristic fallback
    return f"Unable to generate analysis for {ticker}. Please check API configurations."
