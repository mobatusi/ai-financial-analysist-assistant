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
    default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    default_stocks = []
    
    for ticker in default_tickers:
        try:
            data = get_stock_data(ticker)
            if data:
                default_stocks.append({
                    'ticker': ticker,
                    'name': data.get('name', 'N/A'),
                    'price': data.get('price', 0.0),
                    'pct_change': data.get('pct_change', 0.0),
                    'pe_ratio': data.get('pe_ratio', 'N/A'),
                    'beta': data.get('beta', 'N/A')
                })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return render_template("index.html", default_stocks=default_stocks)

# ---------------------------------------------------------------------
# Task 6: Implement DSPy Stock Analysis and Insight Summary Routes
# ---------------------------------------------------------------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    print("--- Received Analyze Request ---")
    data = request.get_json()
    if not data or not data.get("ticker"):
        return jsonify({"status": "error", "message": "Ticker symbol is required"}), 400
    
    ticker = data.get("ticker").upper()
    print(f"Analyzing ticker: {ticker}")
    stock_data = get_stock_data(ticker)
    print(f"Stock data fetched: {bool(stock_data)}")
    
    if not stock_data or stock_data.get("name") == "Error":
        return jsonify({"status": "error", "message": f"No data found for ticker: {ticker}"}), 404
    
    try:
        print("Calling dsp_financial_insight...")
        insight_text = dsp_financial_insight(ticker, stock_data)
        print("Insight generation complete.")
        
        # Store for summary page
        session['latest_analysis'] = {
            'ticker': ticker,
            'company': stock_data.get('name'),
            'price': stock_data.get('price'),
            'change_pct': stock_data.get('pct_change'),
            'pe_ratio': stock_data.get('pe_ratio'),
            'beta': stock_data.get('beta'),
            'insight': insight_text
        }
        
        # Enrich stock_data for the frontend
        stock_data['ticker'] = ticker
        
        return jsonify({
            "status": "ok",
            "stock": stock_data,
            "insight": insight_text
        })
    except Exception as e:
        print(f"Analysis error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/insight_summary")
def insight_summary():
    analysis_data = session.get('latest_analysis')
    
    if not analysis_data:
        return render_template("error.html", message="No DSPy insight is available.")
    
    # Convert markdown insight to HTML
    formatted_insight = markdown.markdown(analysis_data.get('insight', ''))
    
    # Update data with formatted insight for template
    display_data = analysis_data.copy()
    display_data['insight'] = formatted_insight
    
    return render_template("insight_summary.html", insight=display_data)

# Task 7: Implement Portfolio Management Routes
# ---------------------------------------------------------------------

@app.route("/api/portfolio", methods=["POST"])
def add_to_portfolio():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
        
        ticker = data.get("ticker", "").strip().upper()
        quantity_val = data.get("quantity")

        # Validation
        if not ticker:
            return jsonify({"status": "error", "message": "Ticker is required"}), 400
        
        try:
            quantity = float(quantity_val)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Quantity must be a positive number"}), 400

        # Database Operation
        holding = Holding.query.filter_by(ticker=ticker).first()
        if holding:
            holding.quantity += quantity
        else:
            holding = Holding(ticker=ticker, quantity=quantity)
            db.session.add(holding)
        
        db.session.commit()
        return jsonify({"ok": true, "ticker": ticker, "quantity": holding.quantity})

    except Exception as e:
        db.session.rollback()
        print(f"Error in /api/portfolio: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/api/portfolio/delete", methods=["POST"])
def delete_from_portfolio():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
        
        ticker = data.get("ticker", "").strip().upper()

        if not ticker:
            return jsonify({"status": "error", "message": "Ticker is required"}), 400

        holding = Holding.query.filter_by(ticker=ticker).first()
        if not holding:
            return jsonify({"status": "error", "message": "Holding not found"}), 404
        
        db.session.delete(holding)
        db.session.commit()
        return jsonify({"ok": true})

    except Exception as e:
        db.session.rollback()
        print(f"Error in /api/portfolio/delete: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/portfolio")
def portfolio():
    holdings_records = Holding.query.all()
    holdings = []
    total_value = 0.0
    
    for record in holdings_records:
        stock_data = get_stock_data(record.ticker)
        current_price = stock_data.get('price', 0.0)
        value = record.quantity * current_price
        total_value += value
        
        holdings.append({
            'ticker': record.ticker,
            'quantity': record.quantity,
            'price': current_price,
            'value': value
        })
        
    return render_template("portfolio.html", holdings=holdings, total_value=total_value)

@app.route("/history")
def history():
    recent_analyses = AnalysisHistory.query.order_by(AnalysisHistory.created_at.desc()).limit(50).all()
    return render_template("analysis.html", items=recent_analyses)


# ---------------------------------------------------------------------
# Task 8: Implement Portfolio PDF Report Generation Route
# ---------------------------------------------------------------------
@app.route("/report/portfolio.pdf")
def portfolio_report():
    """
    Generates a PDF report of the user's current portfolio holdings.
    """
    holdings_records = Holding.query.all()
    
    # Create a PDF buffer
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2.0, height - 50, "Financial Analyst Assistant - Portfolio Report")
    
    # Timestamp
    p.setFont("Helvetica", 10)
    # Using the current local time provided in the prompt context (though the prompt asks for UTC format)
    # The prompt says: "The generation timestamp in UTC format"
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    p.drawString(50, height - 80, f"Generated on: {timestamp}")
    
    # Table Header
    y = height - 120
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Ticker")
    p.drawString(150, y, "Quantity")
    p.drawString(250, y, "Price")
    p.drawString(350, y, "Value")
    
    y -= 10
    p.line(50, y, width - 50, y)
    
    y -= 25
    p.setFont("Helvetica", 12)
    total_portfolio_value = 0.0
    
    for record in holdings_records:
        stock_data = get_stock_data(record.ticker)
        price = stock_data.get('price', 0.0)
        
        price_display = "N/A"
        value_display = "N/A"
        
        # If price is 0.0 or less, we treat it as invalid/unavailable
        if price > 0:
            value = record.quantity * price
            total_portfolio_value += value
            price_display = f"${price:,.2f}"
            value_display = f"${value:,.2f}"
        
        p.drawString(50, y, record.ticker)
        p.drawString(150, y, f"{record.quantity:,.2f}")
        p.drawString(250, y, price_display)
        p.drawString(350, y, value_display)
        
        y -= 20
        # Check for page overflow
        if y < 100:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 12)
            
    # Portfolio Total
    y -= 20
    p.line(50, y + 15, width - 50, y + 15)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Total Portfolio Value:")
    p.drawString(350, y, f"${total_portfolio_value:,.2f}")
    
    # Finalize PDF
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="portfolio_report.pdf",
        mimetype="application/pdf"
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
