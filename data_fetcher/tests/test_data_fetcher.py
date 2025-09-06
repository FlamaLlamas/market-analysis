"""
Tests for the data fetcher module.
"""

import unittest
import os
import sys
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_fetcher import DataFetcher


class TestDataFetcher(unittest.TestCase):
    """Test cases for DataFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = "test_data"
        self.fetcher = DataFetcher(self.test_data_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def test_directory_creation(self):
        """Test that data directories are created."""
        self.assertTrue(os.path.exists(self.test_data_dir))
        self.assertTrue(os.path.exists(self.fetcher.stocks_dir))
        self.assertTrue(os.path.exists(self.fetcher.options_dir))
    
    def test_fetch_stock_data(self):
        """Test fetching stock data."""
        # Test with SPY (should work)
        data = self.fetcher.fetch_stock_data("SPY", "5d", "1d")
        self.assertIsInstance(data, pd.DataFrame)
        if not data.empty:
            self.assertIn('Symbol', data.columns)
            self.assertIn('Data_Type', data.columns)
            self.assertEqual(data['Symbol'].iloc[0], 'SPY')
            self.assertEqual(data['Data_Type'].iloc[0], 'stock')
    
    def test_fetch_options_data(self):
        """Test fetching options data."""
        # Test with SPY (should work)
        options_data = self.fetcher.fetch_options_data("SPY")
        self.assertIsInstance(options_data, dict)
        if options_data:
            for key, data in options_data.items():
                self.assertIsInstance(data, pd.DataFrame)
                if not data.empty:
                    self.assertIn('Symbol', data.columns)
                    self.assertIn('Option_Type', data.columns)
                    self.assertIn('Data_Type', data.columns)
    
    def test_save_and_load_stock_data(self):
        """Test saving and loading stock data."""
        # Create test data
        test_data = pd.DataFrame({
            'Open': [100, 101],
            'High': [102, 103],
            'Low': [99, 100],
            'Close': [101, 102],
            'Volume': [1000, 1100],
            'Symbol': ['TEST', 'TEST'],
            'Data_Type': ['stock', 'stock']
        })
        
        # Save data
        filepath = self.fetcher.save_stock_data(test_data, "TEST", "5d", "1d")
        self.assertTrue(os.path.exists(filepath))
        
        # Load data
        loaded_data = self.fetcher.load_stock_data(filepath)
        self.assertFalse(loaded_data.empty)
        self.assertEqual(len(loaded_data), 2)
    
    def test_save_and_load_options_data(self):
        """Test saving and loading options data."""
        # Create test options data
        test_options = {
            "2024-01-19_calls": pd.DataFrame({
                'strike': [100, 105],
                'lastPrice': [5.0, 3.0],
                'bid': [4.9, 2.9],
                'ask': [5.1, 3.1],
                'volume': [100, 200],
                'openInterest': [1000, 2000],
                'impliedVolatility': [0.25, 0.30],
                'Symbol': ['TEST', 'TEST'],
                'Option_Type': ['call', 'call'],
                'Data_Type': ['options', 'options']
            })
        }
        
        # Save data
        filepaths = self.fetcher.save_options_data(test_options, "TEST")
        self.assertTrue(len(filepaths) > 0)
        self.assertTrue(os.path.exists(filepaths[0]))
        
        # Load data
        loaded_data = self.fetcher.load_options_data(filepaths[0])
        self.assertFalse(loaded_data.empty)
        self.assertEqual(len(loaded_data), 2)
    
    def test_fetch_and_save_all(self):
        """Test fetching and saving both stock and options data."""
        stock_file, options_files = self.fetcher.fetch_and_save_all("SPY", "5d", "1d")
        
        # Check that files were created
        if stock_file:
            self.assertTrue(os.path.exists(stock_file))
            self.assertIn("stock_data_SPY", stock_file)
        
        if options_files:
            for file in options_files:
                self.assertTrue(os.path.exists(file))
                self.assertIn("options_data_SPY", file)
    
    def test_list_available_data(self):
        """Test listing available data files."""
        # Create some test files
        test_data = pd.DataFrame({
            'Open': [100], 'High': [102], 'Low': [99], 'Close': [101], 'Volume': [1000],
            'Symbol': ['TEST'], 'Data_Type': ['stock']
        })
        
        self.fetcher.save_stock_data(test_data, "TEST", "5d", "1d")
        
        # List available data
        available = self.fetcher.list_available_data()
        self.assertIn('TEST', available)
        self.assertIn('stocks', available['TEST'])
        self.assertIn('options', available['TEST'])


if __name__ == '__main__':
    unittest.main()
