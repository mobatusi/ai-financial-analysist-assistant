import os
import traceback
import logging
from typing import Dict
import dspy
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

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

logging.info(f"OPENAI_API_KEY configured: {bool(OPENAI_API_KEY)}")
if OPENAI_API_KEY:
    logging.info(f"API Key starts with: {OPENAI_API_KEY[:10]}...")

# Initialize DSPy model
try:
    lm = dspy.LM(model="openai/gpt-4", api_key=OPENAI_API_KEY)
    dspy.configure(lm=lm)
    USE_DSPY = True
    logging.info("DSPy initialized successfully")
except Exception as e:
    USE_DSPY = False
    logging.warning(f"DSPy initialization failed: {e}")

# Initialize OpenAI client (fallback option)
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logging.info("OpenAI client initialized successfully")
except Exception as e:
    client = None
    logging.error(f"OpenAI client initialization failed: {e}")

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
    try:
        raw_data = {
            "company": stock_data.get("company"),
            "sector": stock_data.get("sector"),
            "price": stock_data.get("price"),
            "change_pct": stock_data.get("change_pct"),
            "pe_ratio": stock_data.get("pe_ratio"),
            "beta": stock_data.get("beta"),
        }
        raw_summary = "\n".join([f"{k}: {v}" for k, v in raw_data.items()])
        prompt = INSIGHT_PROMPT_TEMPLATE.format(ticker=ticker, raw_summary=raw_summary)

        logging.info(f"Generating insight for {ticker} (USE_DSPY={USE_DSPY}, client={client is not None})")

        # Option 1: DSPy-based Analysis (Preferred)
        if USE_DSPY:
            try:
                logging.info("Attempting DSPy-based analysis...")
                predictor = dspy.Predict("input_text -> analysis_text", llm=lm)
                result = predictor(input_text=prompt)
                logging.info("DSPy analysis successful")
                return getattr(result, "analysis_text", str(result))
            except Exception as e:
                logging.error(f"DSPy analysis failed: {e}")
                traceback.print_exc()

        # Option 2: OpenAI Fallback
        if client and OPENAI_API_KEY:
            try:
                logging.info("Attempting OpenAI fallback...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful financial analyst."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=700,
                )
                logging.info("OpenAI analysis successful")
                return response.choices[0].message.content.strip()
            except Exception as e:
                logging.error(f"OpenAI fallback failed: {e}")
                traceback.print_exc()
        else:
            logging.warning(f"OpenAI client not available (client={client is not None}, key={bool(OPENAI_API_KEY)})")
        # Option 3: Heuristic Fallback (No AI available)
        heuristic_text = (
            f"Analysis for {ticker}:\n"
            f"Price: {stock_data.get('price')}\n"
            f"P/E Ratio: {stock_data.get('pe_ratio')}\n"
            f"Beta: {stock_data.get('beta')}\n\n"
            f"(Insight generation service unavailable. "
            f"Please verify your OPENAI_API_KEY and DSPy setup.)"
        )
        return heuristic_text
    except Exception as e:
        traceback.print_exc()
        return f"Failed to generate insight: {e}"