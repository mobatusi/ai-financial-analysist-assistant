import os
import traceback
import markdown

from io import BytesIO
from datetime import datetime, UTC
from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------
# Tasks 2, 3, and 4: Add Local Imports
# ---------------------------------------------------------------------
from extensions import db
from models import Holding, AnalysisHistory
from utils import get_stock_data
from ai_module import dsp_financial_insight

# ---------------------------------------------------------------------
# Environment Configuration
# ---------------------------------------------------------------------
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_A_RANDOM_VALUE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finance.db")
PORT = int(os.getenv("PORT", 5000))
DEBUG_MODE = os.getenv("FLASK_ENV") == "development"

# ---------------------------------------------------------------------
# Flask Application Setup
# ---------------------------------------------------------------------
import logging

# Configure logging to file
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)


db.init_app(app)

# Ensure tables exist
with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------
# Task 5: Flask Frontend Route Implementation for the AI Financial Analyst Assistant
# ---------------------------------------------------------------------
@app.route("/")
def index():
    """
    Home page displaying live data for default tickers.
    """
    default_tickers = [
        "AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NFLX",
        "JPM", "V", "PG", "NVDA", "ADBE", "CRM", "INTC",
        "CSCO", "PEP", "COST", "KO", "PFE", "MRK", "UNH",
        "HD", "WMT", "DIS", "NKE", "BA", "MCD", "SBUX",
        "IBM", "ORCL", "CMCSA", "T", "VZ", "BABA", "XOM",
        "CVX", "WFC", "GS", "MS", "AXP", "BAC", "PYPL",
        "QCOM", "TXN", "AMAT", "GILD", "BIIB", "LMT", "GE"
    ]

    stocks = []
    for ticker in default_tickers:
        try:
            stocks.append(get_stock_data(ticker))
        except Exception as e:
            print(f"[index] Error fetching {ticker}: {e}")
            stocks.append({
                "ticker": ticker, "company": "N/A", "price": None,
                "change_pct": None, "pe_ratio": None, "beta": None,
                "sector": "N/A"
            })

    return render_template("index.html", default_stocks=stocks)


@app.route("/portfolio")
def portfolio_page():
    """
    Display user's portfolio with live prices and total valuation.
    """
    holdings = Holding.query.order_by(Holding.ticker).all()
    total_value = 0.0
    enriched = []

    for h in holdings:
        try:
            data = get_stock_data(h.ticker)
        except Exception as e:
            print(f"[portfolio_page] Error fetching {h.ticker}: {e}")
            data = {"price": 0.0}

        price = data.get("price") or 0.0
        value = round(price * h.quantity, 2)
        total_value += value

        enriched.append({
            "id": h.id,
            "ticker": h.ticker,
            "quantity": h.quantity,
            "price": price,
            "value": value,
        })

    return render_template("portfolio.html", holdings=enriched, total_value=round(total_value, 2))

@app.route("/history")
def history_page():
    """
    Display recent AI-generated financial analyses.
    """
    items = AnalysisHistory.query.order_by(AnalysisHistory.created_at.desc()).limit(50).all()
    return render_template("analysis.html", items=items)

# ---------------------------------------------------------------------
# Task 6: Implement DSPy Stock Analysis and Insight Summary Routes
# ---------------------------------------------------------------------
@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    Analyze a stock using DSPy and return financial insights.
    """
    try:
        data = request.get_json(force=True)
        ticker = data.get("ticker", "").strip().upper()

        if not ticker:
            return jsonify({"error": "Ticker required"}), 400

        logging.info(f"Analyzing ticker: {ticker}")
        try:
            stock_data = get_stock_data(ticker)
        except Exception as sd_e:
            logging.error(f"get_stock_data failed: {sd_e}")
            raise sd_e

        logging.info(f"Stock data fetched: {stock_data.keys() if stock_data else 'None'}")
        if not stock_data:
            return jsonify({"error": f"No data found for {ticker}"}), 404

        # Generate DSPy insight
        insight = dsp_financial_insight(ticker, stock_data)

        # Save to database for history
        try:
            history_record = AnalysisHistory(
                ticker=ticker,
                analysis=insight
            )
            db.session.add(history_record)
            db.session.commit()
            logging.info(f"Analysis saved to history for {ticker}")
        except Exception as db_error:
            logging.error(f"Failed to save analysis to history: {db_error}")
            # Don't fail the request if history save fails

        # Store in session for summary page
        session["latest_insight"] = {
            "ticker": ticker,
            "company": stock_data.get("company", "N/A"),
            "price": stock_data.get("price", "N/A"),
            "change_pct": stock_data.get("change_pct", "N/A"),
            "pe_ratio": stock_data.get("pe_ratio", "N/A"),
            "beta": stock_data.get("beta", "N/A"),
            "insight": insight
        }

        return jsonify({"status": "ok", "stock": stock_data, "insight": insight})

    except Exception as e:
        logging.error(f"API Analysis Failed: {e}", exc_info=True)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/insight_summary")
def insight_summary():
    insight_data = session.get("latest_insight")
    if not insight_data:
        return render_template("error.html", message="No DSPy insight found. Please analyze a stock first.")
    formatted_text = markdown.markdown(insight_data["insight"])
    insight_data["insight"] = formatted_text
    return render_template("insight_summary.html", insight=insight_data)

# ---------------------------------------------------------------------
# Task 7: Implement Portfolio Management Routes
# ---------------------------------------------------------------------
@app.route("/api/portfolio", methods=["POST"])
def portfolio_api():
    """
    Add or update holdings in the portfolio.
    """
    try:
        data = request.get_json(force=True)
        ticker = data.get("ticker", "").strip().upper()
        qty = float(data.get("quantity", 0))

        if not ticker or qty <= 0:
            return jsonify({"error": "Valid ticker and positive quantity required"}), 400

        holding = Holding.query.filter_by(ticker=ticker).first()
        if holding:
            holding.quantity += qty
        else:
            holding = Holding(ticker=ticker, quantity=qty)
            db.session.add(holding)

        db.session.commit()
        return jsonify({"ok": True, "ticker": ticker, "quantity": holding.quantity})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to update portfolio", "details": str(e)}), 500


@app.route("/api/portfolio/delete", methods=["POST"])
def portfolio_delete():
    """
    Delete a holding from the user's portfolio.
    """
    try:
        data = request.get_json(force=True)
        ticker = data.get("ticker", "").strip().upper()

        if not ticker:
            return jsonify({"error": "Ticker required"}), 400

        holding = Holding.query.filter_by(ticker=ticker).first()
        if not holding:
            return jsonify({"error": f"No record found for {ticker}"}), 404

        db.session.delete(holding)
        db.session.commit()
        return jsonify({"ok": True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to delete", "details": str(e)}), 500

# ---------------------------------------------------------------------
# Task 8: Implement Portfolio PDF Report Generation Route
# ---------------------------------------------------------------------
@app.route("/report/portfolio.pdf")
def portfolio_report():
    """
    Generate and download a portfolio report as a PDF.
    Displays 'N/A' for missing prices but calculates totals correctly.
    """
    try:
        holdings = Holding.query.order_by(Holding.ticker).all()
        total_value = 0.0
        items = []

        for h in holdings:
            try:
                data = get_stock_data(h.ticker)
            except Exception as e:
                print(f"[portfolio_report] Error fetching {h.ticker}: {e}")
                data = {"price": None}

            price = data.get("price")
            qty = h.quantity
            is_valid_price = isinstance(price, (float, int)) and price > 0

            if is_valid_price:
                value = round(price * qty, 2)
                total_value += value
                price_display = f"${price:,.2f}"
                value_display = f"${value:,.2f}"
            else:
                price_display = "N/A"
                value_display = "N/A"

            items.append((h.ticker, qty, price_display, value_display))

        # PDF generation
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 40, "Financial Analyst Assistant - Portfolio Report")
        c.setFont("Helvetica", 10)
        c.drawString(40, height - 60, f"Generated: {datetime.now(UTC):%Y-%m-%d %H:%M:%S UTC}")
        c.drawString(40, height - 75, f"Total Value: ${total_value:,.2f}")

        y = height - 110
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Ticker")
        c.drawString(140, y, "Quantity")
        c.drawString(240, y, "Price")
        c.drawString(340, y, "Value")

        y -= 18
        c.setFont("Helvetica", 10)
        for t, q, p_display, v_display in items:
            if y < 80:
                c.showPage()
                y = height - 60
            c.drawString(40, y, str(t))
            c.drawString(140, y, str(q))
            c.drawString(240, y, str(p_display))
            c.drawString(340, y, str(v_display))
            y -= 16

        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name="portfolio_report.pdf")

    except Exception as e:
        traceback.print_exc()
        return f"Failed to generate report: {e}", 500
        
if __name__ == "__main__":
    # Disable auto-reload to prevent connection resets when library files change
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
