# Data Fetcher

A modular Python tool for fetching and storing historical stock/ETF and options data from Yahoo Finance.

## Features

- **Stock/ETF Data**: Fetch historical price data with customizable periods and intervals
- **Options Data**: Fetch complete options chains with calls and puts for all expirations
- **Organized Storage**: Separate directories for stock and options data
- **Descriptive Filenames**: Clear naming convention that explains what's stored in each file
- **Command Line Interface**: Easy to use from terminal with various options
- **Modular Design**: Can be imported and used in other Python projects

## File Organization

```
data_fetcher/
├── src/
│   ├── __init__.py
│   └── data_fetcher.py          # Main data fetcher module
├── tests/
│   ├── __init__.py
│   └── test_data_fetcher.py     # Unit tests
├── test_simple.py               # Simple test script
└── README.md                    # This file

data/                            # Created when running
├── stocks/                      # Stock/ETF data files
│   └── stock_data_SYMBOL_PERIOD_INTERVAL_TIMESTAMP.csv
└── options/                     # Options data files
    └── options_data_SYMBOL_EXPIRY_TYPE_TIMESTAMP.csv
```

## Filename Conventions

### Stock Data Files
- Format: `stock_data_{SYMBOL}_{PERIOD}_{INTERVAL}_{TIMESTAMP}.csv`
- Example: `stock_data_SPY_2y_1d_20241205_143022.csv`

### Options Data Files
- Format: `options_data_{SYMBOL}_{EXPIRY}_{TYPE}_{TIMESTAMP}.csv`
- Example: `options_data_SPY_20241220_calls_20241205_143022.csv`

## Usage

### Command Line

#### Fetch both stock and options data for multiple symbols:
```bash
cd data_fetcher
python src/data_fetcher.py SPY QQQ --period 2y --interval 1d
```

#### Fetch only stock data:
```bash
python src/data_fetcher.py SPY QQQ --stocks-only --period 1y
```

#### Fetch only options data:
```bash
python src/data_fetcher.py SPY QQQ --options-only
```

#### List available data files:
```bash
python src/data_fetcher.py --list
```

#### Custom data directory:
```bash
python src/data_fetcher.py SPY --data-dir /path/to/custom/data
```

### Python API

```python
from src.data_fetcher import DataFetcher

# Create fetcher instance
fetcher = DataFetcher("my_data")

# Fetch stock data
stock_data = fetcher.fetch_stock_data("SPY", "2y", "1d")

# Fetch options data
options_data = fetcher.fetch_options_data("SPY")

# Save data
stock_file = fetcher.save_stock_data(stock_data, "SPY", "2y", "1d")
options_files = fetcher.save_options_data(options_data, "SPY")

# Load data
loaded_stock = fetcher.load_stock_data(stock_file)
loaded_options = fetcher.load_options_data(options_files[0])
```

## Testing

### Run simple test:
```bash
cd data_fetcher
python test_simple.py
```

### Run unit tests:
```bash
cd data_fetcher
python -m pytest tests/ -v
```

### Run with unittest:
```bash
cd data_fetcher
python -m unittest tests.test_data_fetcher -v
```

## Parameters

### Period Options
- `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

### Interval Options
- `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`

### Supported Symbols
- **ETFs**: SPY, QQQ, IWM, VTI, etc.
- **Stocks**: AAPL, MSFT, TSLA, GOOGL, etc.
- **Indices**: ^GSPC (S&P 500), ^IXIC (NASDAQ), etc.

## Dependencies

- `yfinance`: Yahoo Finance data API
- `pandas`: Data manipulation
- `numpy`: Numerical operations

## Notes

- Options data is fetched for all available expirations
- Each expiration creates separate files for calls and puts
- All data includes metadata (symbol, fetch time, data type)
- Files are timestamped to avoid overwrites
- The tool handles errors gracefully and logs all operations

## 🚀 Commands to Run the Data Fetcher

### 1. **Test the Basic Functionality First:**
```bash
<code_block_to_apply_changes_from>
```

### 2. **Fetch Data for SPY, QQQ, and SPY (2 years of data):**
```bash
cd data_fetcher
python src/data_fetcher.py SPY QQQ --period 2y --interval 1d
```

### 3. **Fetch Only Stock Data:**
```bash
cd data_fetcher
python src/data_fetcher.py SPY QQQ --stocks-only --period 1y
```

### 4. **Fetch Only Options Data:**
```bash
cd data_fetcher
python src/data_fetcher.py SPY QQQ --options-only
```

### 5. **List Available Data Files:**
```bash
cd data_fetcher
python src/data_fetcher.py --list
```

### 6. **Run Unit Tests:**
```bash
cd data_fetcher
python -m unittest tests.test_data_fetcher -v
```

## 📁 File Organization

The data will be stored in:
```
data_fetcher/
├── data/
│   ├── stocks/
│   │   ├── stock_data_SPY_2y_1d_20241205_143022.csv
│   │   └── stock_data_QQQ_2y_1d_20241205_143022.csv
│   └── options/
│       ├── options_data_SPY_20241220_calls_20241205_143022.csv
│       ├── options_data_SPY_20241220_puts_20241205_143022.csv
│       ├── options_data_SPY_20250117_calls_20241205_143022.csv
│       └── options_data_SPY_20250117_puts_20241205_143022.csv
```

##  Key Features

- **Separate Storage**: Stock and options data are stored in separate directories
- **Descriptive Filenames**: Each file clearly indicates what data it contains
- **Timestamped**: Files include timestamps to avoid overwrites
- **Complete Options Data**: Fetches all available expirations with calls and puts
- **Metadata**: All data includes symbol, fetch time, and data type information

Start with the simple test to verify everything is working, then use the main commands to fetch your data!
