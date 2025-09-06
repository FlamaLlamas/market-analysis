# Calendar Diagonal Spread Analyzer

A Streamlit application for analyzing calendar diagonal spreads using options data from Yahoo Finance.

## Features

- Real-time options data from Yahoo Finance
- Black-Scholes option pricing model
- Greeks calculation (Delta, Theta, Vega)
- Interactive P/L visualization
- Support for any stock or ETF with options

## Installation

This project uses Poetry for dependency management.

1. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

## Usage

1. Activate the Poetry environment:
   ```bash
   poetry shell
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

3. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

## Dependencies

- streamlit: Web application framework
- yfinance: Yahoo Finance data API
- numpy: Numerical computing
- matplotlib: Plotting library
- scipy: Scientific computing (for statistical functions)

## How to Use

1. Enter a stock or ETF symbol (e.g., SPY, AAPL, QQQ)
2. Select expiration dates for the short and long legs
3. Choose strike prices for both legs
4. View the calculated Greeks and P/L curve
5. Analyze the risk/reward profile of your calendar diagonal spread

## Requirements

- Python 3.11 or higher
- Internet connection for real-time data 