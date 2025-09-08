import pandas as pd
import numpy as np

# Read the current file
with open('app_backtesting.py', 'r') as f:
    content = f.read()

# Fix 1: Change chart to show actual capital values instead of normalized 100 basis
old_chart_code = """                        # Normalize both to start at 100
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

new_chart_code = """                        # Show actual capital values instead of normalized
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
                        
                        ax.plot(pnl_data.index, strategy_values, label='PUT Spread Strategy', linewidth=2, color='blue')"""

content = content.replace(old_chart_code, new_chart_code)

# Fix 2: Update chart title and y-axis label
old_chart_labels = """                        ax.set_title('Strategy Performance vs SPX', fontsize=16, fontweight='bold')
                        ax.set_xlabel('Date', fontsize=12)
                        ax.set_ylabel('Normalized Value (Base = 100)', fontsize=12)"""

new_chart_labels = """                        ax.set_title('Strategy Performance vs SPX', fontsize=16, fontweight='bold')
                        ax.set_xlabel('Date', fontsize=12)
                        ax.set_ylabel('Portfolio Value ($)', fontsize=12)"""

content = content.replace(old_chart_labels, new_chart_labels)

# Fix 3: Add summary rows every 15 days in trade table
old_trades_display = """                        # Trades summary
                        if results['trades']:
                            st.subheader("📋 Trade Summary")
                            trades_df = pd.DataFrame(results['trades'])
                            st.dataframe(trades_df, use_container_width=True)"""

new_trades_display = """                        # Trades summary with 15-day summaries
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
                                st.dataframe(trades_df, use_container_width=True)"""

content = content.replace(old_trades_display, new_trades_display)

# Write the enhanced file
with open('app_backtesting.py', 'w') as f:
    f.write(content)

print("Enhanced backtest display with actual capital values and 15-day summaries")
