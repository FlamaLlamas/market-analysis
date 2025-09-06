#!/usr/bin/env python3
"""
Simple test script to verify data fetcher is working.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import DataFetcher


def test_basic_functionality():
    """Test basic functionality of the data fetcher."""
    print("Testing DataFetcher basic functionality...")
    
    # Create fetcher instance
    fetcher = DataFetcher("test_data")
    print("✓ DataFetcher created successfully")
    
    # Test fetching stock data for SPY
    print("\nFetching stock data for SPY (5 days)...")
    stock_data = fetcher.fetch_stock_data("SPY", "5d", "1d")
    
    if not stock_data.empty:
        print(f"✓ Fetched {len(stock_data)} stock records for SPY")
        print(f"  Columns: {list(stock_data.columns)}")
        print(f"  Date range: {stock_data.index[0]} to {stock_data.index[-1]}")
    else:
        print("✗ No stock data fetched for SPY")
    
    # Test fetching options data for SPY
    print("\nFetching options data for SPY...")
    options_data = fetcher.fetch_options_data("SPY")
    
    if options_data:
        print(f"✓ Fetched options data for {len(options_data)} expirations")
        for key, data in options_data.items():
            print(f"  {key}: {len(data)} options")
    else:
        print("✗ No options data fetched for SPY")
    
    # Test saving data
    print("\nTesting data saving...")
    if not stock_data.empty:
        stock_file = fetcher.save_stock_data(stock_data, "SPY", "5d", "1d")
        if stock_file:
            print(f"✓ Stock data saved to: {stock_file}")
        else:
            print("✗ Failed to save stock data")
    
    if options_data:
        options_files = fetcher.save_options_data(options_data, "SPY")
        if options_files:
            print(f"✓ Options data saved to {len(options_files)} files")
            for f in options_files[:3]:  # Show first 3 files
                print(f"  {f}")
        else:
            print("✗ Failed to save options data")
    
    print("\n✓ Basic functionality test completed!")


if __name__ == "__main__":
    test_basic_functionality()
