#!/usr/bin/env python3
"""
Test script specifically for SPX data fetching.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import DataFetcher


def test_spx_data():
    """Test SPX data fetching for 1 week."""
    print("Testing SPX data fetching (1 week)...")
    
    # Create fetcher instance
    fetcher = DataFetcher("test_spx_data")
    print("✓ DataFetcher created successfully")
    
    # Test fetching stock data for SPX (1 week)
    print("\nFetching stock data for ^SPX (1 week)...")
    stock_data = fetcher.fetch_stock_data("^SPX", "1w", "1d")
    
    if not stock_data.empty:
        print(f"✓ Fetched {len(stock_data)} stock records for ^SPX")
        print(f"  Columns: {list(stock_data.columns)}")
        print(f"  Date range: {stock_data.index[0]} to {stock_data.index[-1]}")
        print(f"  Latest close: ${stock_data['Close'].iloc[-1]:.2f}")
        print(f"  Price range: ${stock_data['Low'].min():.2f} - ${stock_data['High'].max():.2f}")
    else:
        print("✗ No stock data fetched for ^SPX")
        return False
    
    # Test fetching options data for SPX
    print("\nFetching options data for ^SPX...")
    options_data = fetcher.fetch_options_data("^SPX")
    
    if options_data:
        print(f"✓ Fetched options data for {len(options_data)} option chains")
        total_options = 0
        for key, data in options_data.items():
            print(f"  {key}: {len(data)} options")
            total_options += len(data)
        print(f"  Total options: {total_options}")
        
        # Show sample option data
        if options_data:
            first_key = list(options_data.keys())[0]
            sample_data = options_data[first_key]
            if not sample_data.empty:
                print(f"\n  Sample from {first_key}:")
                print(f"    Columns: {list(sample_data.columns)}")
                if 'strike' in sample_data.columns:
                    print(f"    Strike range: ${sample_data['strike'].min():.2f} - ${sample_data['strike'].max():.2f}")
                if 'lastPrice' in sample_data.columns:
                    print(f"    Price range: ${sample_data['lastPrice'].min():.2f} - ${sample_data['lastPrice'].max():.2f}")
    else:
        print("✗ No options data fetched for ^SPX")
        return False
    
    # Test saving data
    print("\nTesting data saving...")
    if not stock_data.empty:
        stock_file = fetcher.save_stock_data(stock_data, "^SPX", "1w", "1d")
        if stock_file:
            print(f"✓ Stock data saved to: {stock_file}")
        else:
            print("✗ Failed to save stock data")
            return False
    
    if options_data:
        options_files = fetcher.save_options_data(options_data, "^SPX")
        if options_files:
            print(f"✓ Options data saved to {len(options_files)} files")
            print(f"  First few files:")
            for f in options_files[:3]:  # Show first 3 files
                print(f"    {f}")
        else:
            print("✗ Failed to save options data")
            return False
    
    # Test loading data
    print("\nTesting data loading...")
    if stock_file:
        loaded_stock = fetcher.load_stock_data(stock_file)
        if not loaded_stock.empty:
            print(f"✓ Stock data loaded successfully: {len(loaded_stock)} records")
        else:
            print("✗ Failed to load stock data")
            return False
    
    if options_files:
        loaded_options = fetcher.load_options_data(options_files[0])
        if not loaded_options.empty:
            print(f"✓ Options data loaded successfully: {len(loaded_options)} records")
        else:
            print("✗ Failed to load options data")
            return False
    
    print("\n✅ SPX data test completed successfully!")
    print(f"📊 Summary:")
    print(f"  - Stock records: {len(stock_data)}")
    print(f"  - Options chains: {len(options_data)}")
    print(f"  - Total options: {sum(len(data) for data in options_data.values())}")
    print(f"  - Files created: {1 + len(options_files)}")
    
    return True


def test_spx_symbols():
    """Test different SPX symbol formats."""
    print("\n" + "="*50)
    print("Testing different SPX symbol formats...")
    
    symbols_to_test = ['^SPX', 'SPX', '^GSPC']
    fetcher = DataFetcher("test_spx_symbols")
    
    for symbol in symbols_to_test:
        print(f"\n--- Testing {symbol} ---")
        try:
            # Test stock data
            stock_data = fetcher.fetch_stock_data(symbol, "5d", "1d")
            if not stock_data.empty:
                print(f"✓ Stock data: {len(stock_data)} records, Latest: ${stock_data['Close'].iloc[-1]:.2f}")
            else:
                print("✗ No stock data")
            
            # Test options data
            options_data = fetcher.fetch_options_data(symbol)
            if options_data:
                total_options = sum(len(data) for data in options_data.values())
                print(f"✓ Options data: {len(options_data)} chains, {total_options} total options")
            else:
                print("✗ No options data")
                
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("SPX Data Fetcher Test")
    print("=" * 50)
    
    # Test different symbol formats first
    test_spx_symbols()
    
    # Test main functionality
    success = test_spx_data()
    
    if success:
        print("\n🎉 All tests passed! SPX data fetching is working correctly.")
        print("You can now run the full 2-year fetch with confidence.")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        sys.exit(1)
