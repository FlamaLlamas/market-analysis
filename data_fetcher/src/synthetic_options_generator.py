#!/usr/bin/env python3
"""
Synthetic Options Data Generator

Generates synthetic options data using Black-Scholes model and historical volatility
from stock data. Follows the same structure and conventions as data_fetcher.py
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def calculate_historical_volatility(stock_data, window=30):
    """
    Calculate historical volatility from stock data
    
    Args:
        stock_data: DataFrame with stock prices
        window: Rolling window for volatility calculation (default: 30 days)
    
    Returns:
        DataFrame with historical volatility
    """
    # Calculate daily returns
    stock_data['returns'] = np.log(stock_data['Close'] / stock_data['Close'].shift(1))
    
    # Calculate rolling volatility (annualized)
    stock_data['volatility'] = stock_data['returns'].rolling(window=window).std() * np.sqrt(252)
    
    # Fill NaN values with mean volatility
    mean_vol = stock_data['volatility'].mean()
    stock_data['volatility'] = stock_data['volatility'].fillna(mean_vol)
    
    return stock_data

def d1(S, K, T, r, sigma):
    """Black-Scholes d1 calculation"""
    if T <= 0 or sigma <= 0:
        return 0
    return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))

def d2(S, K, T, r, sigma):
    """Black-Scholes d2 calculation"""
    return d1(S, K, T, r, sigma) - sigma*np.sqrt(T)

def bs_call_price(S, K, T, r, sigma):
    """Black-Scholes call option price"""
    if T <= 0:
        return max(S - K, 0) if S > K else 0
    
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(S, K, T, r, sigma)
    
    call_price = S * norm.cdf(d1_val) - K * np.exp(-r*T) * norm.cdf(d2_val)
    return max(call_price, 0)

def bs_put_price(S, K, T, r, sigma):
    """Black-Scholes put option price"""
    if T <= 0:
        return max(K - S, 0) if K > S else 0
    
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(S, K, T, r, sigma)
    
    put_price = K * np.exp(-r*T) * norm.cdf(-d2_val) - S * norm.cdf(-d1_val)
    return max(put_price, 0)

def bs_delta_call(S, K, T, r, sigma):
    """Black-Scholes call delta"""
    if T <= 0:
        return 1 if S > K else 0
    return norm.cdf(d1(S, K, T, r, sigma))

def bs_delta_put(S, K, T, r, sigma):
    """Black-Scholes put delta"""
    if T <= 0:
        return -1 if K > S else 0
    return -norm.cdf(-d1(S, K, T, r, sigma))

def bs_gamma(S, K, T, r, sigma):
    """Black-Scholes gamma"""
    if T <= 0 or sigma <= 0:
        return 0
    d1_val = d1(S, K, T, r, sigma)
    return norm.pdf(d1_val) / (S * sigma * np.sqrt(T))

def bs_theta_call(S, K, T, r, sigma):
    """Black-Scholes call theta"""
    if T <= 0:
        return 0
    
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(S, K, T, r, sigma)
    
    theta = (-S * norm.pdf(d1_val) * sigma / (2 * np.sqrt(T)) - 
             r * K * np.exp(-r*T) * norm.cdf(d2_val))
    return theta / 365  # Convert to daily theta

def bs_theta_put(S, K, T, r, sigma):
    """Black-Scholes put theta"""
    if T <= 0:
        return 0
    
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(S, K, T, r, sigma)
    
    theta = (-S * norm.pdf(d1_val) * sigma / (2 * np.sqrt(T)) + 
             r * K * np.exp(-r*T) * norm.cdf(-d2_val))
    return theta / 365  # Convert to daily theta

def bs_vega(S, K, T, r, sigma):
    """Black-Scholes vega"""
    if T <= 0 or sigma <= 0:
        return 0
    d1_val = d1(S, K, T, r, sigma)
    return S * norm.pdf(d1_val) * np.sqrt(T) / 100  # Vega per 1% change in IV

def generate_strikes(spot_price, num_strikes=20, strike_range=0.3):
    """
    Generate strike prices around current spot price
    
    Args:
        spot_price: Current stock price
        num_strikes: Number of strikes to generate
        strike_range: Range as percentage (0.3 = 30% above/below spot)
    
    Returns:
        List of strike prices
    """
    min_strike = spot_price * (1 - strike_range)
    max_strike = spot_price * (1 + strike_range)
    
    # Generate strikes with more density around ATM
    strikes = []
    
    # ITM strikes (below spot)
    itm_strikes = np.linspace(min_strike, spot_price * 0.95, num_strikes // 3)
    strikes.extend(itm_strikes)
    
    # ATM strikes (around spot)
    atm_strikes = np.linspace(spot_price * 0.95, spot_price * 1.05, num_strikes // 3)
    strikes.extend(atm_strikes)
    
    # OTM strikes (above spot)
    otm_strikes = np.linspace(spot_price * 1.05, max_strike, num_strikes // 3)
    strikes.extend(otm_strikes)
    
    # Round to nearest 5 for SPX
    strikes = [round(strike / 5) * 5 for strike in strikes]
    
    return sorted(list(set(strikes)))

def generate_expirations(current_date, num_expirations=8):
    """
    Generate expiration dates
    
    Args:
        current_date: Current trading date
        num_expirations: Number of expiration dates to generate
    
    Returns:
        List of expiration dates
    """
    expirations = []
    
    # Short-term expirations (weekly)
    for i in range(1, 4):
        exp_date = current_date + timedelta(days=7*i)
        # Round to nearest Friday (SPX expiration)
        days_to_friday = (4 - exp_date.weekday()) % 7
        if days_to_friday == 0:
            days_to_friday = 7
        exp_date = exp_date + timedelta(days=days_to_friday)
        expirations.append(exp_date)
    
    # Medium-term expirations (monthly)
    for i in range(1, 4):
        exp_date = current_date + timedelta(days=30*i)
        # Round to third Friday of month
        first_day = exp_date.replace(day=1)
        first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
        third_friday = first_friday + timedelta(days=14)
        expirations.append(third_friday)
    
    # Long-term expirations (quarterly)
    for i in range(1, 3):
        exp_date = current_date + timedelta(days=90*i)
        # Round to third Friday of quarter
        quarter_month = ((exp_date.month - 1) // 3) * 3 + 1
        quarter_start = exp_date.replace(month=quarter_month, day=1)
        first_friday = quarter_start + timedelta(days=(4 - quarter_start.weekday()) % 7)
        third_friday = first_friday + timedelta(days=14)
        expirations.append(third_friday)
    
    return sorted(expirations)

def generate_synthetic_options(stock_data, symbol, risk_free_rate=0.05):
    """
    Generate synthetic options data for all trading days
    
    Args:
        stock_data: DataFrame with stock prices and volatility
        symbol: Stock symbol
        risk_free_rate: Risk-free interest rate
    
    Returns:
        Dictionary with synthetic options data
    """
    synthetic_data = {}
    
    for date, row in stock_data.iterrows():
        if pd.isna(row['volatility']):
            continue
            
        spot_price = row['Close']
        volatility = row['volatility']
        
        # Generate strikes and expirations
        strikes = generate_strikes(spot_price)
        expirations = generate_expirations(date)
        
        # Generate options for each expiration
        for expiry in expirations:
            days_to_expiry = (expiry - date).days
            if days_to_expiry <= 0:
                continue
                
            T = days_to_expiry / 365.0
            
            # Generate calls and puts
            calls = []
            puts = []
            
            for strike in strikes:
                # Calculate theoretical prices and Greeks
                call_price = bs_call_price(spot_price, strike, T, risk_free_rate, volatility)
                put_price = bs_put_price(spot_price, strike, T, risk_free_rate, volatility)
                
                call_delta = bs_delta_call(spot_price, strike, T, risk_free_rate, volatility)
                put_delta = bs_delta_put(spot_price, strike, T, risk_free_rate, volatility)
                
                gamma = bs_gamma(spot_price, strike, T, risk_free_rate, volatility)
                call_theta = bs_theta_call(spot_price, strike, T, risk_free_rate, volatility)
                put_theta = bs_theta_put(spot_price, strike, T, risk_free_rate, volatility)
                vega = bs_vega(spot_price, strike, T, risk_free_rate, volatility)
                
                # Add some realistic bid-ask spread and volume
                spread = max(0.05, call_price * 0.02)  # 2% spread, minimum $0.05
                call_bid = max(0, call_price - spread/2)
                call_ask = call_price + spread/2
                put_bid = max(0, put_price - spread/2)
                put_ask = put_price + spread/2
                
                # Generate realistic volume and open interest
                volume = np.random.randint(0, 1000)
                open_interest = np.random.randint(100, 5000)
                
                # Call option
                call_data = {
                    'contractSymbol': f'{symbol}{expiry.strftime("%y%m%d")}C{strike:08.0f}',
                    'strike': strike,
                    'lastPrice': call_price,
                    'bid': call_bid,
                    'ask': call_ask,
                    'volume': volume,
                    'openInterest': open_interest,
                    'impliedVolatility': volatility,
                    'delta': call_delta,
                    'gamma': gamma,
                    'theta': call_theta,
                    'vega': vega,
                    'expirationDate': expiry,
                    'lastTradeDate': date
                }
                calls.append(call_data)
                
                # Put option
                put_data = {
                    'contractSymbol': f'{symbol}{expiry.strftime("%y%m%d")}P{strike:08.0f}',
                    'strike': strike,
                    'lastPrice': put_price,
                    'bid': put_bid,
                    'ask': put_ask,
                    'volume': volume,
                    'openInterest': open_interest,
                    'impliedVolatility': volatility,
                    'delta': put_delta,
                    'gamma': gamma,
                    'theta': put_theta,
                    'vega': vega,
                    'expirationDate': expiry,
                    'lastTradeDate': date
                }
                puts.append(put_data)
            
            # Store data
            date_str = date.strftime('%Y%m%d')
            expiry_str = expiry.strftime('%Y%m%d')
            
            if date_str not in synthetic_data:
                synthetic_data[date_str] = {}
            
            synthetic_data[date_str][f'{expiry_str}_calls'] = calls
            synthetic_data[date_str][f'{expiry_str}_puts'] = puts
    
    return synthetic_data

def save_synthetic_options(synthetic_data, symbol, data_dir):
    """
    Save synthetic options data to CSV files
    
    Args:
        synthetic_data: Dictionary with synthetic options data
        symbol: Stock symbol
        data_dir: Data directory path
    """
    options_dir = os.path.join(data_dir, 'options')
    os.makedirs(options_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for date_str, date_data in synthetic_data.items():
        for option_type, options in date_data.items():
            if not options:
                continue
                
            # Extract expiry from option_type
            expiry_str = option_type.split('_')[0]
            option_kind = option_type.split('_')[1]  # calls or puts
            
            # Create filename
            filename = f'options_data_{symbol}_{expiry_str}_{option_kind}_synthetic_{timestamp}.csv'
            filepath = os.path.join(options_dir, filename)
            
            # Save to CSV
            df = pd.DataFrame(options)
            df.to_csv(filepath, index=False)
            
            logger.info(f'Saved {len(options)} {option_kind} for {symbol} {expiry_str} on {date_str}')

def load_stock_data(symbol, data_dir):
    """
    Load stock data from CSV files
    
    Args:
        symbol: Stock symbol
        data_dir: Data directory path
    
    Returns:
        DataFrame with stock data
    """
    stocks_dir = os.path.join(data_dir, 'stocks')
    if not os.path.exists(stocks_dir):
        raise FileNotFoundError(f"Stocks directory not found: {stocks_dir}")
    
    files = [f for f in os.listdir(stocks_dir) if f.startswith(f'stock_data_{symbol}')]
    if not files:
        raise FileNotFoundError(f"No stock data found for {symbol}")
    
    # Get the most recent file
    latest_file = sorted(files)[-1]
    file_path = os.path.join(stocks_dir, latest_file)
    
    logger.info(f"Loading stock data from: {latest_file}")
    
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    df.set_index('Date', inplace=True)
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic options data using Black-Scholes model')
    parser.add_argument('symbols', nargs='+', help='Stock/ETF symbols to generate options for')
    parser.add_argument('--data-dir', default='data', help='Data directory (default: data)')
    parser.add_argument('--volatility-window', type=int, default=30, help='Volatility calculation window (default: 30)')
    parser.add_argument('--risk-free-rate', type=float, default=0.05, help='Risk-free rate (default: 0.05)')
    parser.add_argument('--test-days', type=int, help='Generate options for only first N days (for testing)')
    
    args = parser.parse_args()
    
    for symbol in args.symbols:
        try:
            logger.info(f"Generating synthetic options for {symbol}")
            
            # Load stock data
            stock_data = load_stock_data(symbol, args.data_dir)
            
            # Calculate historical volatility
            stock_data = calculate_historical_volatility(stock_data, args.volatility_window)
            
            # Limit to test days if specified
            if args.test_days:
                stock_data = stock_data.head(args.test_days)
                logger.info(f"Limited to first {args.test_days} days for testing")
            
            # Generate synthetic options
            synthetic_data = generate_synthetic_options(stock_data, symbol, args.risk_free_rate)
            
            # Save synthetic options
            save_synthetic_options(synthetic_data, symbol, args.data_dir)
            
            logger.info(f"Successfully generated synthetic options for {symbol}")
            
        except Exception as e:
            logger.error(f"Error generating synthetic options for {symbol}: {e}")
            continue

if __name__ == '__main__':
    main()
