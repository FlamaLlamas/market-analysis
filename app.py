import streamlit as st
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.stats import norm

st.set_page_config(layout="wide")
st.title("Calendar Diagonal Spread Analyzer")

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

# --- Main app ---

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

# Plot P/L curve at short expiry - zoomed in view
price_range = np.linspace(500, 800, 200)  # Fixed range 500-800

def payoff_at_expiry(price, strike):
    return np.maximum(price - strike, 0)

pl_curve = []
for p in price_range:
    # Short option at expiry: either expires worthless or we pay intrinsic value
    short_payoff = payoff_at_expiry(p, short_strike)
    
    # Long option at short expiry: still has time value remaining
    # Calculate remaining time to long expiry
    T_remaining = T_long - T_short
    
    if T_remaining > 0:
        # Long option still has time value - use Black-Scholes
        long_val = bs_call_price(p, long_strike, T_remaining, r, long_sigma)
    else:
        # Long option also expires (shouldn't happen in calendar spread)
        long_val = payoff_at_expiry(p, long_strike)
    
    # P/L = Long option value - Short option payoff - Initial net debit
    pl = long_val - short_payoff - net_premium
    pl_curve.append(pl)

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

# Recalculate P/L curve for new range
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
st.caption(" **Zoom Controls**: Use the dropdown above to change zoom level. You can also use mouse wheel to zoom in/out on the chart.")

st.pyplot(fig)
