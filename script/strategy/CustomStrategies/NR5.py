import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import atr

class Strategy_NR5(Strategy):
    strategy_name = 'NR5'
    indicator_config = {}

    def __init__(self, symbol_list='NASDAQ', update_new=False, period='2y'):
        super().__init__(symbol_list, update_new, period)
        self.timeframe = '1d'

    def indicator_calculations(self, data):
        data['NR']=data['High'] - data['Low']
        atr(data)
        return data

    def buy_signal(self, data):
        data['NR_Max'] = data['NR'].rolling(window=5).min()
        data['Signal'] = np.where(
            (data['NR'] == data['NR_Max']) &
            (data['High'] < data['High'].shift(1))& # Price Breakout
            (data['High'] > data['Open'].shift(1)) # Give up if Gap
            ,True,False)
        data['Buy Price'] = data['High']
        data.drop(columns=['NR_Max'], inplace=True)
        return data

    def sell_signal(self, data):
        # No sell signal for this strategy
        data['Sell'] = False
        return data

    def stop_profit_loss(self, data):
        data['Stop Profit'] = data['Buy Price'] + data['20-ATR'] * 0.6
        data['Stop Loss'] = data['Buy Price'] - data['20-ATR'] * 0.3
        return data