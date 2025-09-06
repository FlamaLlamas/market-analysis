"""
Data fetcher module for downloading and storing historical stock/ETF and options data.
"""

import yfinance as yf
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Class to fetch and store historical data for stocks/ETFs and options."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the DataFetcher.
        
        Args:
            data_dir: Directory to store CSV files
        """
        self.data_dir = data_dir
        self.stocks_dir = os.path.join(data_dir, "stocks")
        self.options_dir = os.path.join(data_dir, "options")
        self._ensure_data_dirs()
    
    def _ensure_data_dirs(self):
        """Create data directories if they don't exist."""
        for directory in [self.data_dir, self.stocks_dir, self.options_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
    
    def fetch_stock_data(self, 
                        symbol: str, 
                        period: str = "2y", 
                        interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical stock/ETF data.
        
        Args:
            symbol: Stock/ETF symbol (e.g., 'SPY', 'QQQ', 'SPX')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            DataFrame with historical data
        """
        try:
            logger.info(f"Fetching stock data for {symbol} (period: {period}, interval: {interval})")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No stock data found for {symbol}")
                return pd.DataFrame()
            
            # Add metadata
            data['Symbol'] = symbol
            data['Fetched_At'] = datetime.now()
            data['Data_Type'] = 'stock'
            data['Period'] = period
            data['Interval'] = interval
            
            logger.info(f"Successfully fetched {len(data)} stock records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_options_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch options data for a symbol.
        
        Args:
            symbol: Stock/ETF symbol
        
        Returns:
            Dictionary with expirations as keys and option chains as values
        """
        try:
            logger.info(f"Fetching options data for {symbol}")
            ticker = yf.Ticker(symbol)
            
            # Get available expirations
            expirations = ticker.options
            if not expirations:
                logger.warning(f"No options data found for {symbol}")
                return {}
            
            options_data = {}
            for expiry in expirations:
                try:
                    logger.info(f"Fetching options chain for {symbol} expiry: {expiry}")
                    chain = ticker.option_chain(expiry)
                    
                    # Process calls
                    calls = chain.calls.copy()
                    calls['Option_Type'] = 'call'
                    calls['Symbol'] = symbol
                    calls['Expiry'] = expiry
                    calls['Fetched_At'] = datetime.now()
                    calls['Data_Type'] = 'options'
                    
                    # Process puts
                    puts = chain.puts.copy()
                    puts['Option_Type'] = 'put'
                    puts['Symbol'] = symbol
                    puts['Expiry'] = expiry
                    puts['Fetched_At'] = datetime.now()
                    puts['Data_Type'] = 'options'
                    
                    # Store separately
                    options_data[f"{expiry}_calls"] = calls
                    options_data[f"{expiry}_puts"] = puts
                    
                    logger.info(f"Fetched {len(calls)} calls and {len(puts)} puts for {symbol} {expiry}")
                    
                except Exception as e:
                    logger.error(f"Error fetching options for {symbol} {expiry}: {e}")
                    continue
            
            logger.info(f"Successfully fetched options data for {symbol} with {len(options_data)} option chains")
            return options_data
            
        except Exception as e:
            logger.error(f"Error fetching options data for {symbol}: {e}")
            return {}
    
    def save_stock_data(self, data: pd.DataFrame, symbol: str, period: str, interval: str = "1d") -> str:
        """
        Save stock data to CSV file with descriptive filename.
        
        Args:
            data: DataFrame to save
            symbol: Stock/ETF symbol
            period: Data period
            interval: Data interval
        
        Returns:
            Path to saved file
        """
        if data.empty:
            logger.warning(f"No stock data to save for {symbol}")
            return ""
        
        # Create descriptive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_data_{symbol}_{period}_{interval}_{timestamp}.csv"
        filepath = os.path.join(self.stocks_dir, filename)
        
        try:
            data.to_csv(filepath)
            logger.info(f"Stock data saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving stock data for {symbol}: {e}")
            return ""
    
    def save_options_data(self, options_data: Dict[str, pd.DataFrame], symbol: str) -> List[str]:
        """
        Save options data to separate CSV files with descriptive filenames.
        
        Args:
            options_data: Dictionary with option chains as keys and DataFrames as values
            symbol: Stock/ETF symbol
        
        Returns:
            List of paths to saved files
        """
        if not options_data:
            logger.warning(f"No options data to save for {symbol}")
            return []
        
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for key, data in options_data.items():
            if data.empty:
                continue
                
            # Create descriptive filename
            # key format: "YYYY-MM-DD_calls" or "YYYY-MM-DD_puts"
            expiry_clean = key.replace('-', '').replace('_', '_')
            filename = f"options_data_{symbol}_{expiry_clean}_{timestamp}.csv"
            filepath = os.path.join(self.options_dir, filename)
            
            try:
                data.to_csv(filepath, index=False)
                saved_files.append(filepath)
                logger.info(f"Options data saved to: {filepath}")
            except Exception as e:
                logger.error(f"Error saving options data for {symbol} {key}: {e}")
        
        return saved_files
    
    def load_stock_data(self, filepath: str) -> pd.DataFrame:
        """
        Load stock data from CSV file.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            DataFrame with loaded data
        """
        try:
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            logger.info(f"Stock data loaded from: {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading stock data from {filepath}: {e}")
            return pd.DataFrame()
    
    def load_options_data(self, filepath: str) -> pd.DataFrame:
        """
        Load options data from CSV file.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            DataFrame with loaded data
        """
        try:
            data = pd.read_csv(filepath, parse_dates=['Fetched_At'])
            logger.info(f"Options data loaded from: {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading options data from {filepath}: {e}")
            return pd.DataFrame()
    
    def fetch_and_save_all(self, 
                          symbol: str, 
                          period: str = "2y", 
                          interval: str = "1d") -> Tuple[str, List[str]]:
        """
        Fetch both stock and options data and save to separate CSV files.
        
        Args:
            symbol: Stock/ETF symbol
            period: Data period for stock data
            interval: Data interval for stock data
        
        Returns:
            Tuple of (stock_file_path, list_of_options_file_paths)
        """
        # Fetch stock data
        stock_data = self.fetch_stock_data(symbol, period, interval)
        stock_file = self.save_stock_data(stock_data, symbol, period, interval) if not stock_data.empty else ""
        
        # Fetch options data
        options_data = self.fetch_options_data(symbol)
        options_files = self.save_options_data(options_data, symbol) if options_data else []
        
        return stock_file, options_files
    
    def fetch_multiple_symbols(self, 
                              symbols: List[str], 
                              period: str = "2y", 
                              interval: str = "1d") -> Dict[str, Dict[str, any]]:
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of stock/ETF symbols
            period: Data period
            interval: Data interval
        
        Returns:
            Dictionary with results for each symbol
        """
        results = {}
        for symbol in symbols:
            logger.info(f"Processing {symbol}...")
            stock_file, options_files = self.fetch_and_save_all(symbol, period, interval)
            results[symbol] = {
                'stock_file': stock_file,
                'options_files': options_files,
                'stock_records': len(self.load_stock_data(stock_file)) if stock_file else 0,
                'options_records': sum(len(self.load_options_data(f)) for f in options_files)
            }
        return results
    
    def get_latest_files(self, symbol: str) -> Dict[str, str]:
        """
        Get the most recent files for a symbol.
        
        Args:
            symbol: Stock/ETF symbol
        
        Returns:
            Dictionary with 'stock' and 'options' keys
        """
        try:
            # Get latest stock file
            stock_files = [f for f in os.listdir(self.stocks_dir) if f.startswith(f"stock_data_{symbol}_")]
            stock_file = None
            if stock_files:
                stock_files.sort(reverse=True)
                stock_file = os.path.join(self.stocks_dir, stock_files[0])
            
            # Get latest options files
            options_files = [f for f in os.listdir(self.options_dir) if f.startswith(f"options_data_{symbol}_")]
            options_file = None
            if options_files:
                options_files.sort(reverse=True)
                options_file = os.path.join(self.options_dir, options_files[0])
            
            return {
                'stock': stock_file,
                'options': options_file
            }
        except Exception as e:
            logger.error(f"Error finding latest files for {symbol}: {e}")
            return {'stock': None, 'options': None}
    
    def list_available_data(self) -> Dict[str, Dict[str, List[str]]]:
        """
        List all available data files organized by symbol and type.
        
        Returns:
            Dictionary with symbols as keys and file lists as values
        """
        try:
            available_data = {}
            
            # Get stock files
            stock_files = [f for f in os.listdir(self.stocks_dir) if f.endswith('.csv')]
            for file in stock_files:
                # Parse filename: stock_data_SYMBOL_PERIOD_INTERVAL_TIMESTAMP.csv
                parts = file.replace('.csv', '').split('_')
                if len(parts) >= 4:
                    symbol = parts[2]
                    if symbol not in available_data:
                        available_data[symbol] = {'stocks': [], 'options': []}
                    available_data[symbol]['stocks'].append(file)
            
            # Get options files
            options_files = [f for f in os.listdir(self.options_dir) if f.endswith('.csv')]
            for file in options_files:
                # Parse filename: options_data_SYMBOL_EXPIRY_TYPE_TIMESTAMP.csv
                parts = file.replace('.csv', '').split('_')
                if len(parts) >= 5:
                    symbol = parts[2]
                    if symbol not in available_data:
                        available_data[symbol] = {'stocks': [], 'options': []}
                    available_data[symbol]['options'].append(file)
            
            return available_data
        except Exception as e:
            logger.error(f"Error listing available data: {e}")
            return {}


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch and store historical stock/ETF and options data")
    parser.add_argument("symbols", nargs="+", help="Stock/ETF symbols to fetch")
    parser.add_argument("--period", default="2y", help="Data period (default: 2y)")
    parser.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
    parser.add_argument("--data-dir", default="data", help="Data directory (default: data)")
    parser.add_argument("--stocks-only", action="store_true", help="Fetch only stock data, skip options")
    parser.add_argument("--options-only", action="store_true", help="Fetch only options data, skip stocks")
    parser.add_argument("--list", action="store_true", help="List available data files")
    
    args = parser.parse_args()
    
    fetcher = DataFetcher(args.data_dir)
    
    if args.list:
        # List available data
        available = fetcher.list_available_data()
        print("\nAvailable data files:")
        for symbol, files in available.items():
            print(f"\n{symbol}:")
            print(f"  Stock files: {len(files['stocks'])}")
            for f in sorted(files['stocks']):
                print(f"    {f}")
            print(f"  Options files: {len(files['options'])}")
            for f in sorted(files['options']):
                print(f"    {f}")
        return
    
    if args.stocks_only:
        # Fetch only stock data
        for symbol in args.symbols:
            stock_data = fetcher.fetch_stock_data(symbol, args.period, args.interval)
            if not stock_data.empty:
                filepath = fetcher.save_stock_data(stock_data, symbol, args.period, args.interval)
                print(f"Stock data for {symbol}: {filepath}")
    elif args.options_only:
        # Fetch only options data
        for symbol in args.symbols:
            options_data = fetcher.fetch_options_data(symbol)
            if options_data:
                files = fetcher.save_options_data(options_data, symbol)
                print(f"Options data for {symbol}: {len(files)} files")
                for f in files:
                    print(f"  {f}")
    else:
        # Fetch both stock and options data
        results = fetcher.fetch_multiple_symbols(args.symbols, args.period, args.interval)
        
        print(f"\nFetched data for {len(results)} symbols:")
        for symbol, result in results.items():
            print(f"\n{symbol}:")
            print(f"  Stock: {result['stock_file']} ({result['stock_records']} records)")
            print(f"  Options: {len(result['options_files'])} files ({result['options_records']} records)")
            for f in result['options_files']:
                print(f"    {f}")


if __name__ == "__main__":
    main()
