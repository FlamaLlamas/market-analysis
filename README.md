# Options Trading Platform

A comprehensive Streamlit application for options analysis, data visualization, and backtesting using both real-time and historical options data.

## Features

### 📊 Options Analyzer
- Real-time options data from Yahoo Finance
- Black-Scholes option pricing model
- Greeks calculation (Delta, Theta, Vega, Gamma)
- Interactive P/L visualization with zoom controls
- Support for any stock or ETF with options

### 📈 Data Visualizer
- Visualize downloaded historical stock and options data
- Interactive charts for price, volume, and options metrics
- Data availability checker for different symbols

### 📊 Options Backtesting
- Complete PUT spread strategy backtesting
- Historical performance analysis with SPX comparison
- P&L tracking, drawdown analysis, and risk metrics
- Synthetic options data generation using Black-Scholes model

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

### Running the Main Application
```bash
poetry run streamlit run app_backtesting.py
```

### Data Fetching
```bash
# Fetch historical stock and options data
poetry run python data_fetcher/src/data_fetcher.py ^SPX --period 2y

# Generate synthetic options data for backtesting
poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX
```

## Data Coverage

### 📊 Available Data

#### **Stock Data**
- **Symbols:** ^SPX, QQQ, SPY
- **Period:** September 6, 2023 to September 5, 2025 (2 years)
- **Frequency:** Daily OHLCV data
- **Source:** Yahoo Finance via yfinance

#### **Options Data**

##### **Real Options Data (from Yahoo Finance)**
- **Date Range:** September 8, 2025 to December 20, 2030
- **Total Files:** 298 files
- **Coverage:** Current market options data with future expirations
- **Use Case:** Live trading and future leap rolling

##### **Synthetic Options Data (Black-Scholes Generated)**
- **Date Range:** September 15, 2023 to January 16, 2026
- **Total Files:** 240 files
- **Coverage:** Historical options data for backtesting
- **Features:** Complete Greeks, realistic pricing, multiple expirations
- **Use Case:** Historical backtesting and strategy validation

### 🎯 Backtesting Strategy Coverage

#### **PUT Spread Strategy Requirements:**
- **Short-term PUTs (15 DTE):** ✅ Available for selling ATM PUTs
- **Long-term PUTs (1 year leaps at ~25 Delta):** ✅ Available for buying and rolling
- **Rolling Coverage:** ✅ Can roll leaps through 2030

#### **Timeline Coverage:**
- **2023-2025 Backtesting:** ✅ Synthetic options data with realistic pricing
- **2025+ Future Rolling:** ✅ Real market options data for leap rolling
- **Complete Strategy:** ✅ Full PUT spread implementation with proper leap management

### 📁 Data Structure

```
data/
├── stocks/
│   ├── stock_data_^SPX_2y_1d_YYYYMMDD_HHMMSS.csv
│   ├── stock_data_QQQ_2y_1d_YYYYMMDD_HHMMSS.csv
│   └── stock_data_SPY_2y_1d_YYYYMMDD_HHMMSS.csv
└── options/
    ├── options_data_^SPX_YYYYMMDD_puts_YYYYMMDD_HHMMSS.csv (real)
    ├── options_data_^SPX_YYYYMMDD_calls_YYYYMMDD_HHMMSS.csv (real)
    ├── options_data_^SPX_YYYYMMDD_puts_synthetic_YYYYMMDD_HHMMSS.csv
    └── options_data_^SPX_YYYYMMDD_calls_synthetic_YYYYMMDD_HHMMSS.csv
```

## Dependencies

- **streamlit:** Web application framework
- **yfinance:** Yahoo Finance data API
- **numpy:** Numerical computing
- **matplotlib:** Plotting library
- **scipy:** Scientific computing (for statistical functions)
- **pandas:** Data manipulation and analysis

## Applications

### 1. Options Analyzer (`app_backtesting.py` - Tab 1)
- Real-time options analysis
- Calendar diagonal spread evaluation
- Interactive P/L visualization with zoom controls

### 2. Data Visualizer (`app_backtesting.py` - Tab 2)
- Visualize downloaded historical data
- Check data availability for different symbols
- Interactive charts for price and options metrics

### 3. Options Backtesting (`app_backtesting.py` - Tab 3)
- PUT spread strategy backtesting
- Historical performance analysis
- SPX comparison and risk metrics
- Synthetic options data integration

## Data Generation Tools

### Historical Data Fetcher
```bash
# Fetch stock and options data
poetry run python data_fetcher/src/data_fetcher.py ^SPX --period 2y

# Options only
poetry run python data_fetcher/src/data_fetcher.py ^SPX --options-only --period 3y
```

### Synthetic Options Generator
```bash
# Generate full synthetic dataset
poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX

# Test with limited days
poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX --test-days 5
```

## Requirements

- Python 3.11 or higher
- Internet connection for real-time data
- Sufficient disk space for historical data storage

## Project Structure

```
options-pl/
├── app_backtesting.py          # Main Streamlit application
├── data_fetcher/               # Data fetching and generation tools
│   ├── src/
│   │   ├── data_fetcher.py     # Historical data fetcher
│   │   └── synthetic_options_generator.py  # Synthetic options generator
│   └── test_*.py              # Test scripts
├── data/                      # Data storage
│   ├── stocks/               # Historical stock data
│   └── options/              # Options data (real + synthetic)
└── pyproject.toml            # Poetry configuration
```

## Getting Started

1. **Install dependencies:** `poetry install`
2. **Fetch data:** `poetry run python data_fetcher/src/data_fetcher.py ^SPX --period 2y`
3. **Generate synthetic options:** `poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX`
4. **Run application:** `poetry run streamlit run app_backtesting.py`
5. **Open browser:** Navigate to http://localhost:8501

## Strategy Implementation

The platform supports a comprehensive PUT spread strategy:
- **Buy:** 1 PUT option ~1 year away at ~25 Delta (closest available)
- **Sell:** 1 PUT at-the-money 15 days to expiry
- **Roll:** Long PUT every 30 days to maintain ~25 Delta
- **Repeat:** New short PUT every 15 days after expiry

All data requirements for this strategy are fully covered by the available dataset.
