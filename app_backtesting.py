import streamlit as st
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime, timedelta
import json
from scipy.stats import norm
import glob

# =============================================================================
# BLACK-SCHOLES PRICING FUNCTIONS
# =============================================================================

def d1(S, K, T, r, sigma):
    """Black-Scholes d1 calculation"""
    if T <= 0 or sigma <= 0:
        return 0
    return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))

def d2(S, K, T, r, sigma):
    """Black-Scholes d2 calculation"""
    return d1(S, K, T, r, sigma) - sigma*np.sqrt(T)

def bs_put_price(S, K, T, r, sigma):
    """Black-Scholes put option price"""
    if T <= 0:
        return max(K - S, 0) if K > S else 0
    
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(S, K, T, r, sigma)
    
    put_price = K * np.exp(-r*T) * norm.cdf(-d2_val) - S * norm.cdf(-d1_val)
    return max(put_price, 0)

def bs_delta_put(S, K, T, r, sigma):
    """Black-Scholes put delta"""
    if T <= 0:
        return -1 if K > S else 0
    return -norm.cdf(-d1(S, K, T, r, sigma))

# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_stock_data(symbol):
    """Load stock data from CSV files with error handling"""
    data_dir = "data/stocks"
    if not os.path.exists(data_dir):
        return None
    
    files = [f for f in os.listdir(data_dir) if f.startswith(f"stock_data_{symbol}")]
    if not files:
        return None
    
    # Get the most recent file
    latest_file = sorted(files)[-1]
    file_path = os.path.join(data_dir, latest_file)
    
    try:
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        st.error(f"Error loading stock data: {e}")
        return None

def build_options_data_index(symbol):
    """Build an index of all available options data by trading date"""
    data_dir = "data/options"
    if not os.path.exists(data_dir):
        return {}
    
    # Get all synthetic files
    synthetic_files = glob.glob(os.path.join(data_dir, f"options_data_{symbol}_*_synthetic_*.csv"))
    
    options_index = {}
    
    for file_path in synthetic_files:
        try:
            df = pd.read_csv(file_path)
            if 'lastTradeDate' in df.columns:
                df['lastTradeDate'] = pd.to_datetime(df['lastTradeDate'], utc=True)
                # Convert to date for comparison (remove time component)
                trading_date = df['lastTradeDate'].dt.date.iloc[0]
                
                # Separate puts and calls
                if '_puts_' in file_path:
                    options_index[trading_date] = options_index.get(trading_date, {})
                    options_index[trading_date]['puts'] = df
                elif '_calls_' in file_path:
                    options_index[trading_date] = options_index.get(trading_date, {})
                    options_index[trading_date]['calls'] = df
                    
        except Exception as e:
            continue
    
    return options_index

def load_options_data_for_date(options_index, target_date):
    """Load options data for a specific date from the pre-built index"""
    # Convert target_date to date object if it's a datetime
    if hasattr(target_date, 'date'):
        target_date_obj = target_date.date()
    else:
        target_date_obj = target_date
    
    if target_date_obj in options_index:
        data = options_index[target_date_obj]
        return data.get('puts'), data.get('calls')
    
    return None, None

def get_available_data_range(symbol):
    """Get the available data range for a symbol"""
    stock_data = load_stock_data(symbol)
    if stock_data is None:
        return None, None, "No stock data available"
    
    min_date = stock_data.index.min().date()
    max_date = stock_data.index.max().date()
    
    # Build options index to get actual trading dates
    options_index = build_options_data_index(symbol)
    
    if options_index:
        options_dates = sorted(options_index.keys())
        options_min = options_dates[0]
        options_max = options_dates[-1]
        return options_min, options_max, f"Stock: {min_date} to {max_date}, Options: {options_min} to {options_max} ({len(options_dates)} trading days)"
    
    return min_date, max_date, f"Stock: {min_date} to {max_date}, No options data"

# =============================================================================
# OPTIONS SELECTION FUNCTIONS
# =============================================================================

def find_closest_delta_put(options_data, target_delta, spot_price, days_to_expiry, risk_free_rate=0.05):
    """Find PUT option closest to target delta"""
    if options_data is None or options_data.empty:
        return None
    
    best_option = None
    best_delta_diff = float('inf')
    
    for _, option in options_data.iterrows():
        try:
            strike = option['strike']
            implied_vol = option.get('impliedVolatility', 0.2)
            
            # Calculate theoretical delta
            T = days_to_expiry / 365.0
            theoretical_delta = bs_delta_put(spot_price, strike, T, risk_free_rate, implied_vol)
            
            delta_diff = abs(theoretical_delta - target_delta)
            
            if delta_diff < best_delta_diff:
                best_delta_diff = delta_diff
                best_option = option.copy()
                best_option['theoretical_delta'] = theoretical_delta
                
        except Exception as e:
            continue
    
    return best_option

def find_atm_put(options_data, spot_price, days_to_expiry):
    """Find at-the-money PUT option"""
    if options_data is None or options_data.empty:
        return None
    
    # Find closest strike to spot price
    options_data['strike_diff'] = abs(options_data['strike'] - spot_price)
    atm_option = options_data.loc[options_data['strike_diff'].idxmin()].copy()
    
    return atm_option

# =============================================================================
# BACKTESTING ENGINE
# =============================================================================

def run_put_spread_backtest(symbol, start_date, end_date, initial_capital, 
                           target_delta=-0.25, short_dte=15, roll_frequency=30, 
                           short_frequency=15, risk_free_rate=0.05):
    """
    Run the PUT spread backtesting strategy
    """
    
    # Load stock data
    stock_data = load_stock_data(symbol)
    if stock_data is None:
        return None, "No stock data available for the selected symbol and period"
    
    # Build options data index
    options_index = build_options_data_index(symbol)
    if not options_index:
        return None, "No options data available for backtesting"
    
    # Filter data for backtest period
    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)
    
    if start_dt < stock_data.index.min() or end_dt > stock_data.index.max():
        return None, f"Backtest period outside available data range ({stock_data.index.min().date()} to {stock_data.index.max().date()})"
    
    backtest_data = stock_data[(stock_data.index >= start_dt) & (stock_data.index <= end_dt)]
    
    if backtest_data.empty:
        return None, "No data available for the selected period"
    
    # Get available options trading dates in the backtest period
    available_options_dates = [date for date in options_index.keys() 
                              if start_dt.date() <= date <= end_dt.date()]
    
    if not available_options_dates:
        return None, f"No options data available for the selected period ({start_date} to {end_date})"
    
    # Find overlapping dates between stock and options data
    # FIXED: Convert stock index to date objects for proper comparison
    stock_dates = set(backtest_data.index.date)
    overlapping_dates = [date for date in available_options_dates if date in stock_dates]
    
    if not overlapping_dates:
        return None, f"No overlapping dates between stock and options data for the selected period"
    
    st.write(f"Found {len(overlapping_dates)} trading days with both stock and options data in the backtest period")
    
    # Initialize tracking variables
    portfolio_value = initial_capital
    long_put = None
    short_put = None
    trades = []
    daily_pnl = []
    
    # Strategy state tracking
    last_roll_date = None
    last_short_date = None
    
    # Progress tracking
    progress_bar = st.progress(0)
    total_days = len(overlapping_dates)
    
    st.write(f"Running backtest from {start_date} to {end_date}")
    st.write(f"Strategy: Long PUT (~{target_delta} Delta, roll every {roll_frequency} days), Short PUT ({short_dte} DTE, every {short_frequency} days)")
    
    # Process each trading day with both stock and options data
    for i, trading_date in enumerate(sorted(overlapping_dates)):
        # Update progress
        progress_bar.progress((i + 1) / total_days)
        
        # Get stock price for this date - FIXED: Find the exact timestamp
        stock_timestamp = None
        for ts in backtest_data.index:
            if ts.date() == trading_date:
                stock_timestamp = ts
                break
        
        if stock_timestamp is None:
            continue
            
        spot_price = backtest_data.loc[stock_timestamp, 'Close']
        
        # Load options data for current date
        puts_df, calls_df = load_options_data_for_date(options_index, trading_date)
        
        if puts_df is None or puts_df.empty:
            continue
        
        # =================================================================
        # LONG PUT MANAGEMENT (Roll every 30 days)
        # =================================================================
        if (long_put is None or 
            (last_roll_date is None or (trading_date - last_roll_date).days >= roll_frequency)):
            
            # Find long PUT ~1 year out, closest to target delta
            long_expiry = trading_date + timedelta(days=365)
            long_dte = 365
            
            new_long_put = find_closest_delta_put(puts_df, target_delta, spot_price, long_dte, risk_free_rate)
            
            if new_long_put is not None:
                # Close existing long PUT if any
                if long_put is not None:
                    # Mark to market the old position
                    try:
                        T = (long_put['expiry'] - trading_date).days / 365.0
                        iv = long_put.get('impliedVolatility', 0.2)
                        theoretical_value = bs_put_price(spot_price, long_put['strike'], T, risk_free_rate, iv)
                        close_pnl = (theoretical_value - long_put['entry_price']) * 100
                        portfolio_value += close_pnl
                        
                        trades.append({
                            'date': trading_date,
                            'type': 'long_put_roll',
                            'action': 'close',
                            'strike': long_put['strike'],
                            'pnl': close_pnl,
                            'spot': spot_price
                        })
                    except:
                        pass
                
                # Open new long PUT
                new_long_put['entry_date'] = trading_date
                new_long_put['entry_price'] = new_long_put['lastPrice']
                new_long_put['expiry'] = long_expiry
                long_put = new_long_put
                last_roll_date = trading_date
                
                # Deduct cost from portfolio
                portfolio_value -= long_put['entry_price'] * 100
                
                trades.append({
                    'date': trading_date,
                    'type': 'long_put_roll',
                    'action': 'open',
                    'strike': long_put['strike'],
                    'price': long_put['entry_price'],
                    'delta': long_put.get('theoretical_delta', target_delta),
                    'spot': spot_price
                })
        
        # =================================================================
        # SHORT PUT MANAGEMENT (Every 15 days)
        # =================================================================
        if (long_put is not None and 
            (last_short_date is None or (trading_date - last_short_date).days >= short_frequency)):
            
            # Find ATM PUT with ~15 DTE
            new_short_put = find_atm_put(puts_df, spot_price, short_dte)
            
            if new_short_put is not None:
                # Close existing short PUT if any
                if short_put is not None:
                    # Mark to market the old position
                    try:
                        T = (short_put['expiry'] - trading_date).days / 365.0
                        iv = short_put.get('impliedVolatility', 0.2)
                        theoretical_value = bs_put_price(spot_price, short_put['strike'], T, risk_free_rate, iv)
                        close_pnl = (short_put['entry_price'] - theoretical_value) * 100
                        portfolio_value += close_pnl
                        
                        trades.append({
                            'date': trading_date,
                            'type': 'short_put_roll',
                            'action': 'close',
                            'strike': short_put['strike'],
                            'pnl': close_pnl,
                            'spot': spot_price
                        })
                    except:
                        pass
                
                # Open new short PUT
                new_short_put['entry_date'] = trading_date
                new_short_put['entry_price'] = new_short_put['lastPrice']
                new_short_put['expiry'] = trading_date + timedelta(days=short_dte)
                short_put = new_short_put
                last_short_date = trading_date
                
                # Add premium to portfolio
                portfolio_value += short_put['entry_price'] * 100
                
                trades.append({
                    'date': trading_date,
                    'type': 'short_put_roll',
                    'action': 'open',
                    'strike': short_put['strike'],
                    'price': short_put['entry_price'],
                    'spot': spot_price
                })
        
        # =================================================================
        # EXPIRATION MANAGEMENT
        # =================================================================
        if short_put is not None and trading_date >= short_put['expiry']:
            # Short PUT expired
            if spot_price < short_put['strike']:
                # Assigned - buy back at intrinsic value
                intrinsic_value = short_put['strike'] - spot_price
                portfolio_value -= intrinsic_value * 100
                pnl = (short_put['entry_price'] - intrinsic_value) * 100
            else:
                # Expired worthless
                pnl = short_put['entry_price'] * 100
            
            trades.append({
                'date': trading_date,
                'type': 'short_put_expiry',
                'strike': short_put['strike'],
                'spot': spot_price,
                'pnl': pnl,
                'assigned': spot_price < short_put['strike']
            })
            
            short_put = None
        
        # =================================================================
        # PORTFOLIO VALUATION
        # =================================================================
        current_portfolio_value = portfolio_value
        
        # Mark long PUT to market
        if long_put is not None:
            try:
                T = (long_put['expiry'] - trading_date).days / 365.0
                iv = long_put.get('impliedVolatility', 0.2)
                theoretical_value = bs_put_price(spot_price, long_put['strike'], T, risk_free_rate, iv)
                long_put_mtm = (theoretical_value - long_put['entry_price']) * 100
                current_portfolio_value += long_put_mtm
            except:
                pass
        
        # Mark short PUT to market
        if short_put is not None:
            try:
                T = (short_put['expiry'] - trading_date).days / 365.0
                iv = short_put.get('impliedVolatility', 0.2)
                theoretical_value = bs_put_price(spot_price, short_put['strike'], T, risk_free_rate, iv)
                short_put_mtm = (short_put['entry_price'] - theoretical_value) * 100
                current_portfolio_value += short_put_mtm
            except:
                pass
        
        daily_pnl.append({
            'date': trading_date,
            'portfolio_value': current_portfolio_value,
            'spot_price': spot_price,
            'long_put_strike': long_put['strike'] if long_put is not None else None,
            'short_put_strike': short_put['strike'] if short_put is not None else None
        })
    
    progress_bar.progress(1.0)
    
    # Calculate final metrics
    if not daily_pnl:
        return None, "No trades executed during the backtest period"
    
    df_pnl = pd.DataFrame(daily_pnl)
    df_pnl["date"] = pd.to_datetime(df_pnl["date"], utc=True)
    df_pnl.set_index('date', inplace=True)
    
    # Calculate returns and metrics
    df_pnl['returns'] = df_pnl['portfolio_value'].pct_change()
    df_pnl['cumulative_return'] = (df_pnl['portfolio_value'] / initial_capital - 1) * 100
    
    # Calculate drawdown
    df_pnl['peak'] = df_pnl['portfolio_value'].expanding().max()
    df_pnl['drawdown'] = (df_pnl['portfolio_value'] / df_pnl['peak'] - 1) * 100
    
    # SPX comparison - align dates properly
    # Get SPX data for the same dates as our strategy
    spx_dates = []
    spx_prices = []
    
    for date in df_pnl.index:
        # Find the closest SPX trading date
        date_obj = date.date() if hasattr(date, 'date') else date
        closest_spx_date = None
        closest_price = None
        
        for spx_date in backtest_data.index:
            if spx_date.date() == date_obj:
                closest_spx_date = spx_date
                closest_price = backtest_data.loc[spx_date, 'Close']
                break
        
        if closest_price is not None:
            spx_dates.append(date)
            spx_prices.append(closest_price)
    
    # Create aligned SPX data
    spx_data_aligned = pd.DataFrame({
        'Close': spx_prices
    }, index=spx_dates)
    
    spx_returns = spx_data_aligned['Close'].pct_change()
    spx_cumulative = (spx_data_aligned['Close'] / spx_data_aligned['Close'].iloc[0] - 1) * 100
    
    # Calculate final metrics
    total_return = (df_pnl['portfolio_value'].iloc[-1] / initial_capital - 1) * 100
    spx_total_return = spx_cumulative.iloc[-1] if not pd.isna(spx_cumulative.iloc[-1]) else 0
    max_drawdown = df_pnl['drawdown'].min()
    
    # Sharpe ratio (simplified)
    strategy_sharpe = df_pnl['returns'].mean() / df_pnl['returns'].std() * np.sqrt(252) if df_pnl['returns'].std() > 0 else 0
    spx_sharpe = spx_returns.mean() / spx_returns.std() * np.sqrt(252) if spx_returns.std() > 0 else 0
    
    results = {
        'pnl_data': df_pnl,
        'trades': trades,
        'metrics': {
            'total_return': total_return,
            'spx_total_return': spx_total_return,
            'max_drawdown': max_drawdown,
            'strategy_sharpe': strategy_sharpe,
            'spx_sharpe': spx_sharpe,
            'final_portfolio_value': df_pnl['portfolio_value'].iloc[-1],
            'initial_capital': initial_capital,
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in trades if t.get('pnl', 0) < 0]),
            'trades_with_pnl': len([t for t in trades if 'pnl' in t and t['pnl'] is not None])
        },
        'spx_data': spx_data_aligned
    }
    
    return results, None

# =============================================================================
# STREAMLIT APPLICATION
# =============================================================================

def main():
    st.set_page_config(page_title="Final Fixed Options Trading Platform", layout="wide")
    
    st.title("📊 Final Fixed Options Trading Platform")
    st.markdown("**PUT Spread Strategy Backtesting with Corrected Date Matching**")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Options Analyzer", "📈 Data Visualizer", "📊 Final Fixed Backtesting"])
    
    with tab1:
        st.header("📊 Options Analyzer")
        st.write("Real-time options analysis and calendar diagonal spread evaluation.")
        st.info("This tab will be enhanced with the original options analyzer functionality.")
    
    with tab2:
        st.header("📈 Data Visualizer")
        
        # Symbol selection
        symbol = st.selectbox("Select Symbol", ["^SPX", "QQQ", "SPY"], index=0)
        
        # Load and display available data
        data_dir = "data"
        if os.path.exists(data_dir):
            st.subheader("Available Data")
            
            # Stock data
            stocks_dir = os.path.join(data_dir, "stocks")
            if os.path.exists(stocks_dir):
                stock_files = [f for f in os.listdir(stocks_dir) if f.startswith(f"stock_data_{symbol}")]
                if stock_files:
                    st.write(f"**Stock Data for {symbol}:**")
                    for file in sorted(stock_files):
                        st.write(f"- {file}")
                else:
                    st.write(f"No stock data found for {symbol}")
            
            # Options data
            options_index = build_options_data_index(symbol)
            if options_index:
                options_dates = sorted(options_index.keys())
                st.write(f"**Options Data for {symbol}:**")
                st.write(f"- **Synthetic Options:** {len(options_dates)} trading days")
                st.write(f"- **Date Range:** {options_dates[0]} to {options_dates[-1]}")
                st.write(f"- **Sample Dates:** {options_dates[:5]} ... {options_dates[-5:]}")
            else:
                st.write(f"No options data found for {symbol}")
        else:
            st.write("No data directory found. Please run the data fetcher first.")
    
    with tab3:
        st.header("📊 Final Fixed PUT Spread Backtesting")
        
        # Strategy description
        st.markdown("""
        **PUT Spread Strategy:**
        - Buy 1 PUT option ~1 year away at ~25 Delta (closest available)
        - Sell 1 PUT at-the-money 15 days to expiry
        - Record P&L at expiry
        - Sell another ATM PUT 15 days to expiry
        - Roll the long PUT every 30 days to maintain ~25 Delta
        """)
        
        # Input parameters
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.selectbox("Symbol", ["^SPX", "QQQ", "SPY"], index=0, key="backtest_symbol")
            
            # Get available data range
            min_date, max_date, data_info = get_available_data_range(symbol)
            
            if min_date and max_date:
                st.write(f"**Available Data:** {data_info}")
                
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
                end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
            else:
                st.error(f"No data available for {symbol}")
                start_date = None
                end_date = None
        
        with col2:
            initial_capital = st.number_input("Initial Capital ($)", value=10000, min_value=1000, step=1000)
            
            # Strategy parameters
            st.subheader("Strategy Parameters")
            target_delta = st.slider("Target Delta for Long PUT", -0.5, -0.1, -0.25, 0.05)
            short_dte = st.slider("Short PUT DTE", 10, 30, 15, 1)
            roll_frequency = st.slider("Roll Frequency (days)", 20, 60, 30, 5)
            short_frequency = st.slider("Short PUT Frequency (days)", 10, 30, 15, 1)
        
        # Run backtest button
        if st.button("🚀 Run Final Fixed Backtest", type="primary"):
            if start_date and end_date and start_date < end_date:
                with st.spinner("Running final fixed backtest..."):
                    results, error = run_put_spread_backtest(
                        symbol, start_date, end_date, initial_capital,
                        target_delta, short_dte, roll_frequency, short_frequency
                    )
                    
                    if error:
                        st.error(error)
                    else:
                        # Display results
                        st.success("✅ Final fixed backtest completed successfully!")
                        
                        # Metrics summary
                        metrics = results['metrics']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Return", f"{metrics['total_return']:.2f}%")
                        with col2:
                            st.metric("SPX Return", f"{metrics['spx_total_return']:.2f}%")
                        with col3:
                            st.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")
                        with col4:
                            st.metric("Final Value", f"${metrics['final_portfolio_value']:,.2f}")
                        
                        # Additional metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Trades", metrics['total_trades'])
                        with col2:
                            st.metric("Winning Trades", metrics['winning_trades'])
                        with col3:
                            st.metric("Losing Trades", metrics['losing_trades'])
                        with col4:
                            trades_with_pnl = metrics.get('trades_with_pnl', metrics['total_trades'])
                            win_rate = (metrics['winning_trades'] / trades_with_pnl * 100) if trades_with_pnl > 0 else 0
                            st.metric("Win Rate", f"{win_rate:.1f}%")
                        
                        # P&L Chart
                        st.subheader("📈 Portfolio Performance vs SPX")
                        fig, ax = plt.subplots(figsize=(14, 8))
                        
                        pnl_data = results['pnl_data']
                        spx_data = results['spx_data']
                        
                        # Show actual capital values instead of normalized
                        strategy_values = pnl_data['portfolio_value']
                        
                        # Calculate SPX equivalent investment
                        if len(spx_data) > 0 and not spx_data['Close'].isna().all():
                            spx_start_price = spx_data['Close'].iloc[0]
                            spx_shares = initial_capital / spx_start_price
                            spx_values = spx_data['Close'] * spx_shares
                            ax.plot(spx_data.index, spx_values, label='SPX Buy & Hold', linewidth=2, alpha=0.7, color='orange')
                        else:
                            # Fallback: use backtest_data directly
                            spx_fallback = backtest_data.reindex(pnl_data.index, method='ffill')
                            if len(spx_fallback) > 0 and not spx_fallback['Close'].isna().all():
                                spx_start_price = spx_fallback['Close'].iloc[0]
                                spx_shares = initial_capital / spx_start_price
                                spx_values = spx_fallback['Close'] * spx_shares
                                ax.plot(spx_fallback.index, spx_values, label='SPX Buy & Hold', linewidth=2, alpha=0.7, color='orange')
                        
                        ax.plot(pnl_data.index, strategy_values, label='PUT Spread Strategy', linewidth=2, color='blue')
                        
                        ax.set_title('Strategy Performance vs SPX', fontsize=16, fontweight='bold')
                        ax.set_xlabel('Date', fontsize=12)
                        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
                        ax.legend(fontsize=12)
                        ax.grid(True, alpha=0.3)
                        
                        st.pyplot(fig)
                        
                        # Drawdown Chart
                        st.subheader("📉 Drawdown Analysis")
                        fig2, ax2 = plt.subplots(figsize=(14, 6))
                        
                        ax2.fill_between(pnl_data.index, pnl_data['drawdown'], 0, alpha=0.3, color='red')
                        ax2.plot(pnl_data.index, pnl_data['drawdown'], color='red', linewidth=1)
                        
                        ax2.set_title('Strategy Drawdown', fontsize=16, fontweight='bold')
                        ax2.set_xlabel('Date', fontsize=12)
                        ax2.set_ylabel('Drawdown (%)', fontsize=12)
                        ax2.grid(True, alpha=0.3)
                        
                        st.pyplot(fig2)
                        
                        # Trades summary with 15-day summaries
                        if results['trades']:
                            st.subheader("📋 Trade Summary")
                            trades_df = pd.DataFrame(results['trades'])
                            
                            # Add 15-day summary rows
                            summary_rows = []
                            current_date = None
                            period_start_date = None
                            period_trades = []
                            period_pnl = 0
                            period_capital = initial_capital
                            
                            for _, trade in trades_df.iterrows():
                                trade_date = pd.to_datetime(trade['date'])
                                
                                # Check if we need to start a new 15-day period
                                if current_date is None or (trade_date - current_date).days >= 15:
                                    # Save previous period summary if it exists
                                    if period_start_date is not None and len(period_trades) > 0:
                                        period_return = (period_pnl / period_capital * 100) if period_capital > 0 else 0
                                        summary_rows.append({
                                            'date': f"{period_start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}",
                                            'type': 'PERIOD_SUMMARY',
                                            'action': '15-Day Summary',
                                            'strike': f"Capital: ${period_capital:,.0f}",
                                            'price': f"P&L: ${period_pnl:,.0f}",
                                            'delta': f"Return: {period_return:.1f}%",
                                            'spot': f"Trades: {len(period_trades)}"
                                        })
                                    
                                    # Start new period
                                    period_start_date = trade_date
                                    period_trades = []
                                    period_pnl = 0
                                
                                current_date = trade_date
                                period_trades.append(trade)
                                
                                # Update period P&L and capital
                                if 'pnl' in trade and pd.notna(trade['pnl']):
                                    period_pnl += trade['pnl']
                                    period_capital += trade['pnl']
                            
                            # Add final period summary
                            if period_start_date is not None and len(period_trades) > 0:
                                period_return = (period_pnl / period_capital * 100) if period_capital > 0 else 0
                                summary_rows.append({
                                    'date': f"{period_start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}",
                                    'type': 'PERIOD_SUMMARY',
                                    'action': '15-Day Summary',
                                    'strike': f"Capital: ${period_capital:,.0f}",
                                    'price': f"P&L: ${period_pnl:,.0f}",
                                    'delta': f"Return: {period_return:.1f}%",
                                    'spot': f"Trades: {len(period_trades)}"
                                })
                            
                            # Combine original trades with summary rows
                            if summary_rows:
                                summary_df = pd.DataFrame(summary_rows)
                                combined_df = pd.concat([trades_df, summary_df], ignore_index=True)
                                # Sort by date
                                combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
                                combined_df = combined_df.sort_values('date')
                                combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')
                                st.dataframe(combined_df, use_container_width=True)
                            else:
                                st.dataframe(trades_df, use_container_width=True)
                        
                        # Save results
                        results_file = f"final_fixed_backtest_results_{symbol}_{start_date}_{end_date}.json"
                        results_to_save = {
                            'symbol': symbol,
                            'start_date': start_date.isoformat(),
                            'end_date': end_date.isoformat(),
                            'initial_capital': initial_capital,
                            'strategy_params': {
                                'target_delta': target_delta,
                                'short_dte': short_dte,
                                'roll_frequency': roll_frequency,
                                'short_frequency': short_frequency
                            },
                            'metrics': metrics,
                            'data_info': data_info
                        }
                        
                        with open(results_file, 'w') as f:
                            json.dump(results_to_save, f, indent=2)
                        
                        st.success(f"📁 Results saved to {results_file}")
            else:
                st.error("Please select valid start and end dates")

if __name__ == "__main__":
    main()
