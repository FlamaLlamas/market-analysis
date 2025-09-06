# Options PL - Setup and Run Guide

This guide will help you set up and run both the Streamlit options analyzer app and the data fetcher tool.

## 📋 Prerequisites

- Python 3.11 or higher
- Poetry (Python dependency manager)

## 🚀 Quick Setup

### 1. Install Poetry (if not already installed)
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies
```bash
# Install all dependencies including dev dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 3. Verify Installation
```bash
# Check that all packages are installed
poetry show

# Test the data fetcher
poetry run test-data-fetcher
```

## 🎯 Running the Streamlit App

### Option 1: Using Poetry Run
```bash
poetry run streamlit run app.py
```

### Option 2: Using Poetry Shell
```bash
poetry shell
streamlit run app.py
```

### Option 3: Using the Helper Script
```bash
poetry run python run.py
```

The app will be available at: **http://localhost:8501**

## 📊 Running the Data Fetcher

### Test the Data Fetcher First
```bash
# Run simple test
poetry run test-data-fetcher

# Or run the test script directly
poetry run python data_fetcher/test_simple.py
```

### Fetch Data for SPY, QQQ (2 years)
```bash
# Fetch both stock and options data
poetry run data-fetcher SPY QQQ --period 2y --interval 1d

# Or run directly
poetry run python data_fetcher/src/data_fetcher.py SPY QQQ --period 2y --interval 1d
```

### Fetch Only Stock Data
```bash
poetry run data-fetcher SPY QQQ --stocks-only --period 1y
```

### Fetch Only Options Data
```bash
poetry run data-fetcher SPY QQQ --options-only
```

### List Available Data
```bash
poetry run data-fetcher --list
```

## 🧪 Running Tests

### Run Data Fetcher Tests
```bash
# Run unit tests
poetry run python -m unittest data_fetcher.tests.test_data_fetcher -v

# Run with pytest (if installed)
poetry run pytest data_fetcher/tests/ -v
```

### Run All Tests
```bash
poetry run pytest . -v
```

## 📁 Project Structure

```
options-pl/
├── app.py                          # Main Streamlit app
├── run.py                          # Helper script to run app
├── pyproject.toml                  # Poetry configuration
├── poetry.lock                     # Locked dependencies
├── README.md                       # Main project README
├── SETUP_AND_RUN.md               # This file
├── data_fetcher/                   # Data fetcher module
│   ├── src/
│   │   ├── __init__.py
│   │   └── data_fetcher.py        # Main data fetcher
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_data_fetcher.py   # Unit tests
│   ├── test_simple.py             # Simple test script
│   ├── README.md                  # Data fetcher documentation
│   └── data/                      # Generated data files
│       ├── stocks/                # Stock/ETF data
│       └── options/               # Options data
└── .gitignore                     # Git ignore file
```

## 🔧 Development Commands

### Code Formatting
```bash
# Format code with black
poetry run black .

# Check code style
poetry run flake8 .
```

### Update Dependencies
```bash
# Update all dependencies
poetry update

# Add new dependency
poetry add package-name

# Add dev dependency
poetry add --group dev package-name
```

### Environment Management
```bash
# Show environment info
poetry env info

# Show installed packages
poetry show

# Remove virtual environment
poetry env remove python
```

## 🐛 Troubleshooting

### Common Issues

1. **Poetry not found**
   ```bash
   # Add Poetry to PATH
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Python version issues**
   ```bash
   # Check Python version
   python3 --version
   
   # Use specific Python version
   poetry env use python3.11
   ```

3. **Permission issues**
   ```bash
   # Fix Poetry permissions
   poetry config virtualenvs.in-project true
   ```

4. **Streamlit warnings**
   - The ScriptRunContext warnings are harmless and can be ignored
   - The pandas FutureWarning has been fixed in the code

### Reset Everything
```bash
# Remove virtual environment
poetry env remove python

# Remove lock file
rm poetry.lock

# Reinstall everything
poetry install
```

## 📝 Usage Examples

### Streamlit App Usage
1. Open browser to http://localhost:8501
2. Enter stock symbol (e.g., SPY, AAPL, QQQ)
3. Select expiration dates
4. Choose strike prices
5. View P/L analysis and Greeks
6. Use zoom controls for detailed view

### Data Fetcher Usage
```bash
# Fetch 1 year of daily data for SPY
poetry run data-fetcher SPY --period 1y --interval 1d

# Fetch 6 months of hourly data for QQQ
poetry run data-fetcher QQQ --period 6mo --interval 1h

# Fetch options data only for AAPL
poetry run data-fetcher AAPL --options-only

# List all available data files
poetry run data-fetcher --list
```

## 🎯 Quick Start Commands

```bash
# 1. Setup
poetry install
poetry shell

# 2. Test data fetcher
poetry run test-data-fetcher

# 3. Fetch some data
poetry run data-fetcher SPY QQQ --period 2y

# 4. Run the app
streamlit run app.py

# 5. Open browser to http://localhost:8501
```

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify all dependencies are installed: `poetry show`
3. Run tests to verify functionality: `poetry run test-data-fetcher`
4. Check the logs for specific error messages
