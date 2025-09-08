import pandas as pd
import numpy as np

# Read the current file
with open('app_backtesting.py', 'r') as f:
    content = f.read()

# Fix 1: SPX data alignment and NaN handling
old_spx_code = """    # SPX comparison - align dates
    spx_data_aligned = backtest_data.reindex(df_pnl.index, method='ffill')
    spx_returns = spx_data_aligned['Close'].pct_change()
    spx_cumulative = (spx_data_aligned['Close'] / spx_data_aligned['Close'].iloc[0] - 1) * 100
    
    # Calculate final metrics
    total_return = (df_pnl['portfolio_value'].iloc[-1] / initial_capital - 1) * 100
    spx_total_return = spx_cumulative.iloc[-1]"""

new_spx_code = """    # SPX comparison - align dates properly
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
    spx_total_return = spx_cumulative.iloc[-1] if not pd.isna(spx_cumulative.iloc[-1]) else 0"""

content = content.replace(old_spx_code, new_spx_code)

# Fix 2: Win rate calculation - only count trades with P&L data
old_winrate_code = """            'winning_trades': len([t for t in trades if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in trades if t.get('pnl', 0) < 0])"""

new_winrate_code = """            'winning_trades': len([t for t in trades if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in trades if t.get('pnl', 0) < 0]),
            'trades_with_pnl': len([t for t in trades if 'pnl' in t and t['pnl'] is not None])"""

content = content.replace(old_winrate_code, new_winrate_code)

# Fix 3: Update win rate calculation in the UI
old_ui_winrate = """                        with col4:
                            win_rate = (metrics['winning_trades'] / metrics['total_trades'] * 100) if metrics['total_trades'] > 0 else 0
                            st.metric("Win Rate", f"{win_rate:.1f}%")"""

new_ui_winrate = """                        with col4:
                            trades_with_pnl = metrics.get('trades_with_pnl', metrics['total_trades'])
                            win_rate = (metrics['winning_trades'] / trades_with_pnl * 100) if trades_with_pnl > 0 else 0
                            st.metric("Win Rate", f"{win_rate:.1f}%")"""

content = content.replace(old_ui_winrate, new_ui_winrate)

# Fix 4: Ensure SPX line shows up in chart
old_chart_code = """                        # Normalize both to start at 100
                        pnl_normalized = (pnl_data['portfolio_value'] / pnl_data['portfolio_value'].iloc[0]) * 100
                        spx_normalized = (spx_data['Close'] / spx_data['Close'].iloc[0]) * 100
                        
                        ax.plot(pnl_data.index, pnl_normalized, label='PUT Spread Strategy', linewidth=2, color='blue')
                        ax.plot(spx_data.index, spx_normalized, label='SPX Buy & Hold', linewidth=2, alpha=0.7, color='orange')"""

new_chart_code = """                        # Normalize both to start at 100
                        pnl_normalized = (pnl_data['portfolio_value'] / pnl_data['portfolio_value'].iloc[0]) * 100
                        
                        # Ensure SPX data is properly aligned and not empty
                        if len(spx_data) > 0 and not spx_data['Close'].isna().all():
                            spx_normalized = (spx_data['Close'] / spx_data['Close'].iloc[0]) * 100
                            ax.plot(spx_data.index, spx_normalized, label='SPX Buy & Hold', linewidth=2, alpha=0.7, color='orange')
                        else:
                            # Fallback: use backtest_data directly
                            spx_fallback = backtest_data.reindex(pnl_data.index, method='ffill')
                            if len(spx_fallback) > 0 and not spx_fallback['Close'].isna().all():
                                spx_normalized = (spx_fallback['Close'] / spx_fallback['Close'].iloc[0]) * 100
                                ax.plot(spx_fallback.index, spx_normalized, label='SPX Buy & Hold', linewidth=2, alpha=0.7, color='orange')
                        
                        ax.plot(pnl_data.index, pnl_normalized, label='PUT Spread Strategy', linewidth=2, color='blue')"""

content = content.replace(old_chart_code, new_chart_code)

# Write the fixed file
with open('app_backtesting.py', 'w') as f:
    f.write(content)

print("Fixed all issues in app_backtesting.py")
