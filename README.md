# AI Financial Analyst Assistant

AI-powered financial analyst assistant using Flask, DSPy, and OpenAI to analyze stock data, optimize portfolios, and generate smart financial reports through an interactive web dashboard.

## Technologies

- **Backend**: Flask (Python)
- **AI Framework**: DSPy
- **LLM**: OpenAI GPT models
- **Data Source**: Yahoo Finance (yfinance)
- **Database**: SQLite (SQLAlchemy)
- **Reporting**: ReportLab (PDF Generation)
- **Frontend**: HTML5, Vanilla CSS, Jinja2

## Project Structure

```text
ai-financial-analysist-assistant/
├── DSPY_GPT/
│   ├── static/             # CSS and static assets
│   ├── templates/          # Jinja2 HTML templates
│   ├── ai_module.py        # DSPy logic and AI signatures
│   ├── app.py              # Flask application entry point
│   ├── extensions.py       # Flask extensions (DB, etc.)
│   ├── models.py           # Database models
│   ├── utils.py            # Financial data retrieval & utility functions
│   └── .env                # Environment variables (API keys)
└── README.md
```

## Features

The project development is broken down into the following key tasks:

### 1. Introduction
- **Task 0**: Get Started
- **Task 1**: Get an Overview of the Financial Analyst Dashboard UI

### 2. Database Integration and Data Utility Functions
- **Task 2**: Create the Response Model
- **Task 3**: Stock Data Utilities

### 3. Flask Routes, DSPy Insights, and Reporting
- **Task 4**: Implement Financial Insight Generation Using DSPy
- **Task 5**: Implement Flask Frontend Route for AI Dashboard
- **Task 6**: Implement DSPy Stock Analysis and Insight Summary Routes
- **Task 7**: Implement Portfolio Management Routes
- **Task 8**: Implement Portfolio PDF Report Generation Route

## Setup Instructions

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/mobatusi/ai-financial-analysist-assistant.git
    cd ai-financial-analysist-assistant
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables**:
    Create a `.env` file in the `DSPY_GPT` directory and add your OpenAI API key:
    ```env
    OPENAI_API_KEY=your_api_key_here
    ```

4.  **Run the application**:
    ```bash
    python DSPY_GPT/app.py
    ```

## Usage

- **Dashboard**: View live stock data and market performance.
- **Analysis**: Enter a stock ticker (e.g., AAPL) to generate AI-powered insights using DSPy.
- **Portfolio**: Manage your holdings by adding or removing stocks and tracking their real-time value.
- **Reports**: Generate PDF reports summarizing your portfolio performance and recent analyses.

## References

- [Build an AI Financial Analyst Assistant Using DSPy and Flask - Educative](https://www.educative.io/projects/build-an-ai-financial-analyst-assistant-using-dspy-and-flask)
- [DSPy Documentation](https://dspy.ai/)
- [DSPy API Reference](https://dspy.ai/api/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [ReportLab PDF Library](https://www.reportlab.com/docs/reportlab-userguide.pdf)
