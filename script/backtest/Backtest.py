import __init__
import logging
import pandas as pd
import datetime
import plotly.graph_objects as go
import os
DIR_BACKTEST_ROOT = 'ouput/backtest'
os.makedirs(DIR_BACKTEST_ROOT,exist_ok=True)
class Backtest():

    def __init__(self, strategy=None, symbol_list='NASDAQ', update_new=False, period=None):
        if strategy is None:
            print("No strategy provided, only backtest functionality availiable")
            return
        if period is None:
            self.strategy = strategy(symbol_list, update_new)
        else:
            self.strategy = strategy(symbol_list, update_new, period)

    def load_data(self):
        print("Loading Data...")
        self.strategy.fetch_data()
        print("Analysing Strategy...")
        self.strategy.analyze()

    def simulate(self, symbol=None, verbose=False, allow_repeat=False, df=None):
        if symbol and df:
            raise("simulate should provide either symbol or df!")
        if symbol is not None:
            # A Pandas Dataframe to perform backtest
            stock_env = self.strategy.data_manager.data.get(symbol)
        elif df is not None:
            stock_env = df
        else:
            raise("simulate should provide either symbol or df!")
        
        record = []
        if symbol == 'NASDAQ' or symbol == 'SP500':
            return self.analyze_all(verbose=verbose)
        if stock_env is None:
            logging.warning("Stock symbol not found when backtesting")
            return
        buy_index = stock_env.loc[stock_env['Signal']].index
        current_index = -1
        for i in buy_index:
            if current_index > i and not allow_repeat: # Prevent buy being executed multiple times (correspond to one trade)
                continue
            if i == len(stock_env) - 1: #Last index is buy
                break
            buy_price = stock_env.iloc[i]['Buy Price']
            stop_profit = stock_env.iloc[i]['Stop Profit']
            stop_loss = stock_env.iloc[i]['Stop Loss']
            buy_date = stock_env.iloc[i+1]['Date']
            if verbose:
                print(f'Buy {symbol} at {buy_price} on {buy_date}')

            sell_tomorrow = False
            sell_price = -1
            trade_end = False
            for k in range(i+1, len(stock_env)):
                current_index = k
                current_high = stock_env.iloc[k]['High']
                current_low = stock_env.iloc[k]['Low']
                current_open = stock_env.iloc[k]['Open']
                current_sell_signal = stock_env.iloc[k]['Sell']
                hold_time = k - i

                # Trigger Sell for case 2
                if sell_tomorrow:
                    sell_price = current_open
                    trade_end = True
                    if verbose:
                        print(f'(Sell Signal)')
                    break

                #Case 1: Stop Profit/ Loss trigger
                if stop_profit and current_high >= stop_profit:
                    sell_price = stop_profit
                    trade_end = True
                    if verbose:
                        print(f'(Stop Profit)')
                    break
                if stop_loss and current_low <= stop_loss:
                    sell_price = stop_loss
                    trade_end = True
                    if verbose:
                        print(f'(Stop Loss)')
                    break

                #Case 2: Sell signal triggers: Sell the stock on next day open
                if current_sell_signal:
                    if verbose:
                        print("(Sell Tomorrow)")
                    sell_tomorrow = True
                    continue

            if trade_end: #Ensure that the trade must end before calculating result
                sell_date = stock_env.iloc[current_index]['Date']
                pct_change = (sell_price - buy_price)/buy_price
                profit = pct_change > 0
                if verbose:
                    print(f'Sell {symbol} at {sell_price} on {sell_date}')
                    print(f'Percentage Change: {round(pct_change*100,2)} Profit: {profit}')
                    print()
                record.append([symbol,buy_date,hold_time,sell_date,buy_price,sell_price,pct_change,profit])
        return {
            'data':stock_env,
            'record':pd.DataFrame(record, columns=['Symbol','Buy Date','Hold Time','Sell Date','Buy Price', 'Sell Price', 'Percentage Change', 'Profit'])
        }

    def analyze_stat(self, simulate_result, graph=True, indicators=[]):
        if simulate_result is None:
            return
        pct_change = simulate_result['record']['Percentage Change']
        profit = simulate_result['record']['Profit']
        hold_time = simulate_result['record']['Hold Time']
        print(f'Total Percentage Change: {pct_change.sum()}')
        print(f"Total Trade: {len(simulate_result['record'])}")
        print(f'Total Win: {profit.sum()}')
        print(f'Win Rate: {profit.mean()}')
        print(f'Average Hold TIme: {hold_time.mean()}')
        if graph:
            self.plot_graph(simulate_result, indicators)

    def plot_graph(self, simulate_result, indicators):
        data = simulate_result['data']
        fig = go.Figure(data=[go.Candlestick(x=data['Date'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'])])

        fig.update_layout(title='Backtest',
                          xaxis=dict(
                        tickmode='auto',  # Automatically determine tick spacing
                        nticks=20,  # Specify the maximum number of ticks to display
                        type='category',  # Use if your x-axis data is categorical (dates as categories)
                        title='Date',
                        rangeslider_visible=True
                        ),
                        yaxis_title='Price')  # Hides the range slider at the bottom
        for key, value in indicators.items():
            fig.add_trace(go.Scatter(x=data['Date'], y=data[key], mode='lines', name=key, line=dict(color=value, width=2)))

        for i in range(len(simulate_result['record'])):
            buy_price = simulate_result['record']['Buy Price'].iloc[i]
            sell_price = simulate_result['record']['Sell Price'].iloc[i]
            # Add a line for the trade result
            line_color = 'purple' if sell_price > buy_price else 'gray'
            fig.add_trace(go.Scatter(x=[simulate_result['record']['Buy Date'].iloc[i], simulate_result['record']['Sell Date'].iloc[i]],
                                    y=[buy_price, sell_price],
                                    mode='lines+markers',
                                    line=dict(color=line_color, width=2),
                                    marker=dict(color=line_color, size=8),
                                    showlegend=False))
        fig.show()

    def analyze_all(self, verbose=True):
        record_all = None
        symbol_list = self.strategy.data_manager.symbol
        for i, symbol in enumerate(symbol_list):
            print(f'{i+1}/{len(symbol_list)} - {symbol}')
            simulate_result = self.simulate(symbol,verbose=False)
            if verbose:
                self.analyze_stat(simulate_result,graph=False)
            if record_all is None:
                record_all = simulate_result['record']
            else:
                if simulate_result and len(simulate_result['record']) > 0:
                    record_all = pd.concat([record_all, simulate_result['record']])
        record_all.to_csv(f'{DIR_BACKTEST_ROOT}/{self.strategy.strategy_name}_{self.strategy.symbol_list}.csv',index=False)
        pct_change = record_all['Percentage Change']
        profit = record_all['Profit']
        hold_time = record_all['Hold Time']

        print(f'Total Percentage Change: {pct_change.sum()}')
        print(f"Total Trade: {len(record_all)}")
        print(f'Total Win: {profit.sum()}')
        print(f'Win Rate: {profit.mean()}')
        print(f'Average Percentage Change: {pct_change.sum()/ len(record_all)}')
        print(f'Average Hold TIme: {hold_time.mean()}')
