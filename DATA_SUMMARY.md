# Data Summary

## Quick Reference

### Stock Data
- **Symbols:** ^SPX, QQQ, SPY
- **Period:** 2023-09-06 to 2025-09-05 (2 years)
- **Files:** 3 stock data files
- **Format:** Daily OHLCV data

### Options Data

#### Real Options (yfinance)
- **Files:** 298 files
- **Period:** 2025-09-08 to 2030-12-20
- **Use:** Live trading, future leap rolling

#### Synthetic Options (Black-Scholes)
- **Files:** 240 files  
- **Period:** 2023-09-15 to 2026-01-16
- **Use:** Historical backtesting

### Total Data Files
- **Stock:** 3 files
- **Options:** 538 files (298 real + 240 synthetic)
- **Total:** 541 data files

### Backtesting Coverage
- **2023-2025:** ✅ Complete (synthetic options)
- **2025+:** ✅ Complete (real options)
- **Strategy:** ✅ Full PUT spread with leap rolling

## Commands

```bash
# Check data
ls -la data/stocks/
ls -la data/options/ | wc -l

# Run backtesting
poetry run streamlit run app_backtesting.py
```
