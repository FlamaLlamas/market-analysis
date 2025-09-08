# Synthetic Options Data Generator

This module generates synthetic options data using the Black-Scholes model and historical volatility calculated from stock data.

## Features

- **Historical Volatility Calculation**: Calculates rolling volatility from stock price data
- **Black-Scholes Pricing**: Generates theoretical option prices using the Black-Scholes model
- **Complete Greeks**: Calculates Delta, Gamma, Theta, and Vega for each option
- **Realistic Data**: Includes bid-ask spreads, volume, and open interest
- **Multiple Expirations**: Generates options with various expiration dates
- **SPX-Compatible**: Generates strikes compatible with SPX options

## Usage

### Generate Synthetic Options for Full Dataset
```bash
poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX
```

### Generate for Testing (First 5 Days)
```bash
poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX --test-days 5
```

### Custom Parameters
```bash
poetry run python data_fetcher/src/synthetic_options_generator.py ^SPX \
    --volatility-window 30 \
    --risk-free-rate 0.05 \
    --test-days 10
```

## Parameters

- `--volatility-window`: Rolling window for volatility calculation (default: 30 days)
- `--risk-free-rate`: Risk-free interest rate (default: 0.05)
- `--test-days`: Generate options for only first N days (for testing)
- `--data-dir`: Data directory (default: data)

## Output

Synthetic options data is saved to `data/options/` with the naming convention:
```
options_data_^SPX_YYYYMMDD_puts_synthetic_YYYYMMDD_HHMMSS.csv
options_data_^SPX_YYYYMMDD_calls_synthetic_YYYYMMDD_HHMMSS.csv
```

## Data Structure

Each options file contains:
- `contractSymbol`: Option contract symbol
- `strike`: Strike price
- `lastPrice`: Theoretical option price
- `bid`/`ask`: Bid-ask spread
- `volume`/`openInterest`: Trading volume and open interest
- `impliedVolatility`: Historical volatility
- `delta`/`gamma`/`theta`/`vega`: Option Greeks
- `expirationDate`: Option expiration date
- `lastTradeDate`: Trading date

## Testing

Run the test script to generate synthetic options for a few days:
```bash
poetry run python data_fetcher/test_synthetic.py
```

## Integration with Backtesting

The synthetic options data can be used with the backtesting system by modifying the data loading functions to look for files with `_synthetic_` in the filename.
