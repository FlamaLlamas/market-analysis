import streamlit as st
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from scipy.stats import norm

st.set_page_config(layout="wide")
st.title("Options Analysis Platform")

# Add tabs
tab1, tab2 = st.tabs(["📊 Options Analyzer", "📈 Data Visualizer"])

# --- Black-Scholes functions to price options and Greeks ---

def d1(S, K, T, r, sigma):
    return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

def d2(S, K, T, r, sigma):
    return d1(S, K, T, r, sigma) - sigma * np.sqrt(T)

def bs_call_price(S, K, T, r, sigma):
    D1 = d1(S, K, T, r, sigma)
    D2 = d2(S, K, T, r, sigma)
    return S * norm.cdf(D1) - K * np.exp(-r * T) * norm.cdf(D2)

def bs_vega(S, K, T, r, sigma):
    D1 = d1(S, K, T, r, sigma)
    return S * norm.pdf(D1) * np.sqrt(T)

def bs_theta(S, K, T, r, sigma):
    D1 = d1(S, K, T, r, sigma)
    D2 = d2(S, K, T, r, sigma)
    term1 = - (S * norm.pdf(D1) * sigma) / (2 * np.sqrt(T))
    term2 = - r * K * np.exp(-r * T) * norm.cdf(D2)
    return term1 + term2

def bs_delta(S, K, T, r, sigma):
    D1 = d1(S, K, T, r, sigma)
    return norm.cdf(D1)

def option_payoff_call(price, strike):
    return np.maximum(price - strike, 0)

# --- Data Visualizer Functions ---

def load_stock_data(filepath):
    """Load stock data from CSV file."""
    try:
        data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        return data
    except Exception as e:
        st.error(f"Error loading stock data: {e}")
        return pd.DataFrame()

def load_options_data(filepath):
    """Load options data from CSV file."""
    try:
        data = pd.read_csv(filepath, parse_dates=['Fetched_At'])
        return data
    except Exception as e:
        st.error(f"Error loading options data: {e}")
        return pd.DataFrame()

def list_available_data():
    """List all available data files."""
    data_dir = "data"
    available_data = {}
    
    if not os.path.exists(data_dir):
        return available_data
    
    # Get stock files
    stocks_dir = os.path.join(data_dir, "stocks")
    if os.path.exists(stocks_dir):
        stock_files = [f for f in os.listdir(stocks_dir) if f.endswith('.csv')]
        for file in stock_files:
            parts = file.replace('.csv', '').split('_')
            if len(parts) >= 4:
                symbol = parts[2]
                if symbol not in available_data:
                    available_data[symbol] = {'stocks': [], 'options': []}
                available_data[symbol]['stocks'].append(file)
    
    # Get options files
    options_dir = os.path.join(data_dir, "options")
    if os.path.exists(options_dir):
        options_files = [f for f in os.listdir(options_dir) if f.endswith('.csv')]
        for file in options_files:
            parts = file.replace('.csv', '').split('_')
            if len(parts) >= 5:
                symbol = parts[2]
                if symbol not in available_data:
                    available_data[symbol] = {'stocks': [], 'options': []}
                available_data[symbol]['options'].append(file)
    
    return available_data

def plot_stock_data(data, symbol):
    """Plot stock price data."""
    if data.empty:
        return None
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Price chart
    ax1.plot(data.index, data['Close'], label='Close Price', linewidth=2)
    ax1.plot(data.index, data['High'], label='High', alpha=0.7, linewidth=1)
    ax1.plot(data.index, data['Low'], label='Low', alpha=0.7, linewidth=1)
    ax1.set_title(f'{symbol} Stock Price History')
    ax1.set_ylabel('Price ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Volume chart
    ax2.bar(data.index, data['Volume'], alpha=0.7, color='orange')
    ax2.set_title(f'{symbol} Trading Volume')
    ax2.set_ylabel('Volume')
    ax2.set_xlabel('Date')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_options_data(data, symbol, expiry):
    """Plot options data."""
    if data.empty:
        return None
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Strike vs Price
    calls = data[data['Option_Type'] == 'call']
    puts = data[data['Option_Type'] == 'put']
    
    if not calls.empty:
        ax1.scatter(calls['strike'], calls['lastPrice'], alpha=0.6, label='Calls', color='green')
    if not puts.empty:
        ax1.scatter(puts['strike'], puts['lastPrice'], alpha=0.6, label='Puts', color='red')
    ax1.set_title(f'{symbol} Options - Strike vs Price ({expiry})')
    ax1.set_xlabel('Strike Price ($)')
    ax1.set_ylabel('Option Price ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Implied Volatility
    if not calls.empty and 'impliedVolatility' in calls.columns:
        ax2.scatter(calls['strike'], calls['impliedVolatility'], alpha=0.6, label='Calls', color='green')
    if not puts.empty and 'impliedVolatility' in puts.columns:
        ax2.scatter(puts['strike'], puts['impliedVolatility'], alpha=0.6, label='Puts', color='red')
    ax2.set_title(f'{symbol} Implied Volatility ({expiry})')
    ax2.set_xlabel('Strike Price ($)')
    ax2.set_ylabel('Implied Volatility')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Volume
    if not calls.empty and 'volume' in calls.columns:
        ax3.bar(calls['strike'], calls['volume'], alpha=0.6, label='Calls', color='green')
    if not puts.empty and 'volume' in puts.columns:
        ax3.bar(puts['strike'], puts['volume'], alpha=0.6, label='Puts', color='red')
    ax3.set_title(f'{symbol} Options Volume ({expiry})')
    ax3.set_xlabel('Strike Price ($)')
    ax3.set_ylabel('Volume')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Open Interest
    if not calls.empty and 'openInterest' in calls.columns:
        ax4.bar(calls['strike'], calls['openInterest'], alpha=0.6, label='Calls', color='green')
    if not puts.empty and 'openInterest' in puts.columns:
        ax4.bar(puts['strike'], puts['openInterest'], alpha=0.6, label='Puts', color='red')
    ax4.set_title(f'{symbol} Open Interest ({expiry})')
    ax4.set_xlabel('Strike Price ($)')
    ax4.set_ylabel('Open Interest')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# --- TAB 1: Options Analyzer (Original functionality) ---

with tab1:
    st.header("📊 Calendar Diagonal Spread Analyzer")
    
    ticker = st.text_input("Enter Stock or ETF Symbol", value="SPY").upper()
    if not ticker:
        st.stop()

    # Fetch stock data and option expirations
    try:
        stock = yf.Ticker(ticker)
        spot_price = stock.history(period="1d")['Close'].iloc[-1]
        expirations = stock.options
        if len(expirations) < 2:
            st.error("Not enough option expirations available for calendar spreads.")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        st.stop()

    st.write(f"**Current price of {ticker}:** ${spot_price:.2f}")

    # Select expirations for short and long legs
    short_expiry = st.selectbox("Select Short Leg Expiry", expirations, index=0)
    long_expiry = st.selectbox("Select Long Leg Expiry", expirations, index=len(expirations)-1)

    if datetime.strptime(long_expiry, '%Y-%m-%d') <= datetime.strptime(short_expiry, '%Y-%m-%d'):
        st.warning("Long leg expiry should be after short leg expiry.")
        st.stop()

    # Load option chains
    short_chain = stock.option_chain(short_expiry)
    long_chain = stock.option_chain(long_expiry)

    # Extract call strikes (you can extend to puts easily)
    short_strikes = sorted(short_chain.calls['strike'].unique())
    long_strikes = sorted(long_chain.calls['strike'].unique())

    # Slider defaults near spot price
    def closest_strike(strikes, price):
        return min(strikes, key=lambda x: abs(x - price))

    default_short_strike = closest_strike(short_strikes, spot_price)
    default_long_strike = closest_strike(long_strikes, spot_price)

    short_strike = st.select_slider("Short Leg Strike (Call)", options=short_strikes, value=default_short_strike)
    long_strike = st.select_slider("Long Leg Strike (Call)", options=long_strikes, value=default_long_strike)

    # Risk-free rate and volatility (simplified assumptions)
    r = 0.03  # 3% annual risk-free
    # Use implied volatility from yfinance if available, else estimate from historical
    short_iv = short_chain.calls.loc[short_chain.calls['strike'] == short_strike, 'impliedVolatility']
    long_iv = long_chain.calls.loc[long_chain.calls['strike'] == long_strike, 'impliedVolatility']

    if short_iv.empty or long_iv.empty:
        st.warning("Could not get implied volatility for selected strikes; using 25% as fallback.")
        short_sigma = 0.25
        long_sigma = 0.25
    else:
        short_sigma = float(short_iv.iloc[0])
        long_sigma = float(long_iv.iloc[0])

    # Calculate time to expiry in years
    today = datetime.today()
    T_short = (datetime.strptime(short_expiry, '%Y-%m-%d') - today).days / 365
    T_long = (datetime.strptime(long_expiry, '%Y-%m-%d') - today).days / 365

    if T_short <= 0 or T_long <= 0:
        st.error("Selected expirations are in the past or today.")
        st.stop()

    # Calculate option premiums using Black-Scholes (theoretical)
    short_premium = bs_call_price(spot_price, short_strike, T_short, r, short_sigma)
    long_premium = bs_call_price(spot_price, long_strike, T_long, r, long_sigma)
    net_premium = long_premium - short_premium

    # Calculate Greeks for each leg
    short_delta = bs_delta(spot_price, short_strike, T_short, r, short_sigma)
    long_delta = bs_delta(spot_price, long_strike, T_long, r, long_sigma)

    short_theta = bs_theta(spot_price, short_strike, T_short, r, short_sigma)
    long_theta = bs_theta(spot_price, long_strike, T_long, r, long_sigma)

    short_vega = bs_vega(spot_price, short_strike, T_short, r, short_sigma)
    long_vega = bs_vega(spot_price, long_strike, T_long, r, long_sigma)

    net_delta = long_delta - short_delta
    net_theta = long_theta - short_theta
    net_vega = long_vega - short_vega

    st.markdown("### Position Summary")
    st.write(f"**Net Debit (Cost):** ${net_premium:.2f}")
    st.write(f"**Net Delta:** {net_delta:.3f}")
    st.write(f"**Net Theta (per year):** {net_theta:.3f}")
    st.write(f"**Net Vega:** {net_vega:.3f}")

    # Plot P/L curve at short expiry - with zoom controls
    def payoff_at_expiry(price, strike):
        return np.maximum(price - strike, 0)

    # Add zoom controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        zoom_level = st.selectbox("Zoom Level", ["Zoomed In (500-800)", "Normal (70%-130% of Spot)", "Wide View (50%-150% of Spot)"], index=0)

    # Adjust price range based on zoom level
    if zoom_level == "Zoomed In (500-800)":
        price_range = np.linspace(500, 800, 200)
        x_min, x_max = 500, 800
        y_min, y_max = -40, 40
    elif zoom_level == "Normal (70%-130% of Spot)":
        price_range = np.linspace(spot_price * 0.7, spot_price * 1.3, 200)
        x_min, x_max = spot_price * 0.7, spot_price * 1.3
        y_min, y_max = None, None
    else:  # Wide View
        price_range = np.linspace(spot_price * 0.5, spot_price * 1.5, 200)
        x_min, x_max = spot_price * 0.5, spot_price * 1.5
        y_min, y_max = None, None

    # Calculate P/L curve for selected range
    pl_curve = []
    for p in price_range:
        short_payoff = payoff_at_expiry(p, short_strike)
        T_remaining = T_long - T_short
        
        if T_remaining > 0:
            long_val = bs_call_price(p, long_strike, T_remaining, r, long_sigma)
        else:
            long_val = payoff_at_expiry(p, long_strike)
        
        pl = long_val - short_payoff - net_premium
        pl_curve.append(pl)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(price_range, pl_curve, label="P/L at Short Expiry", linewidth=2, color='blue')
    ax.axhline(0, color='black', lw=0.7, alpha=0.7)
    ax.axvline(spot_price, color='gray', ls='--', label="Spot Price", alpha=0.7)
    ax.set_xlabel("Underlying Price at Short Expiry")
    ax.set_ylabel("Profit / Loss ($)")
    ax.set_title(f"Calendar Diagonal Spread P/L for {ticker} - {zoom_level}")
    ax.set_xlim(x_min, x_max)
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add zoom instructions
    st.caption("🔍 **Zoom Controls**: Use the dropdown above to change zoom level. You can also use mouse wheel to zoom in/out on the chart.")

    st.pyplot(fig)

# --- TAB 2: Data Visualizer ---

with tab2:
    st.header("📈 Data Visualizer")
    st.write("Visualize and verify your downloaded data")
    
    # List available data
    available_data = list_available_data()
    
    if not available_data:
        st.warning("No data files found. Please run the data fetcher first to download some data.")
        st.info("Use this command to fetch data: `poetry run python data_fetcher/src/data_fetcher.py ^SPX --period 2y --interval 1d`")
    else:
        st.success(f"Found data for {len(available_data)} symbols: {', '.join(available_data.keys())}")
        
        # Symbol selection
        selected_symbol = st.selectbox("Select Symbol", list(available_data.keys()))
        
        if selected_symbol:
            symbol_data = available_data[selected_symbol]
            
            # Display file information
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Stock Files", len(symbol_data['stocks']))
            with col2:
                st.metric("Options Files", len(symbol_data['options']))
            
            # Stock data visualization
            if symbol_data['stocks']:
                st.subheader("📊 Stock Price Data")
                
                # Select stock file
                stock_file = st.selectbox("Select Stock File", symbol_data['stocks'])
                if stock_file:
                    filepath = os.path.join("data/stocks", stock_file)
                    stock_data = load_stock_data(filepath)
                    
                    if not stock_data.empty:
                        # Display basic info
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Records", len(stock_data))
                        with col2:
                            st.metric("Latest Price", f"${stock_data['Close'].iloc[-1]:.2f}")
                        with col3:
                            st.metric("Date Range", f"{stock_data.index[0].strftime('%Y-%m-%d')} to {stock_data.index[-1].strftime('%Y-%m-%d')}")
                        with col4:
                            price_change = ((stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0]) * 100
                            st.metric("Total Return", f"{price_change:.2f}%")
                        
                        # Plot stock data
                        fig = plot_stock_data(stock_data, selected_symbol)
                        if fig:
                            st.pyplot(fig)
                        
                        # Show data table
                        if st.checkbox("Show Stock Data Table"):
                            st.dataframe(stock_data)
                    else:
                        st.error("Failed to load stock data")
            
            # Options data visualization
            if symbol_data['options']:
                st.subheader("📈 Options Data")
                
                # Group options files by expiry
                options_by_expiry = {}
                for file in symbol_data['options']:
                    parts = file.replace('.csv', '').split('_')
                    if len(parts) >= 5:
                        expiry = parts[3]  # Extract expiry from filename
                        if expiry not in options_by_expiry:
                            options_by_expiry[expiry] = []
                        options_by_expiry[expiry].append(file)
                
                if options_by_expiry:
                    # Select expiry
                    selected_expiry = st.selectbox("Select Expiry", list(options_by_expiry.keys()))
                    
                    if selected_expiry:
                        expiry_files = options_by_expiry[selected_expiry]
                        
                        # Load and combine calls and puts for this expiry
                        combined_options = pd.DataFrame()
                        for file in expiry_files:
                            filepath = os.path.join("data/options", file)
                            options_data = load_options_data(filepath)
                            if not options_data.empty:
                                combined_options = pd.concat([combined_options, options_data], ignore_index=True)
                        
                        if not combined_options.empty:
                            # Display options info
                            calls = combined_options[combined_options['Option_Type'] == 'call']
                            puts = combined_options[combined_options['Option_Type'] == 'put']
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Options", len(combined_options))
                            with col2:
                                st.metric("Calls", len(calls))
                            with col3:
                                st.metric("Puts", len(puts))
                            with col4:
                                if 'strike' in combined_options.columns:
                                    st.metric("Strike Range", f"${combined_options['strike'].min():.0f} - ${combined_options['strike'].max():.0f}")
                            
                            # Plot options data
                            fig = plot_options_data(combined_options, selected_symbol, selected_expiry)
                            if fig:
                                st.pyplot(fig)
                            
                            # Show data table
                            if st.checkbox("Show Options Data Table"):
                                st.dataframe(combined_options)
                        else:
                            st.error("Failed to load options data")
                else:
                    st.warning("No options data found for this symbol")
