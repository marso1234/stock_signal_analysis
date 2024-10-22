import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import MACD, ema, atr, keltner_channel
class Strategy_Keltner(Strategy):
    strategy_name = 'Keltner Strategy'
    indicator_config={'5-EMA':'red', 'Keltner_Bottom':'black'}

    def __init__(self, symbol_list='NASDAQ', update_new=False, period='2y'):
        super().__init__(symbol_list, update_new, period)
        self.timeframe = '1d'

    def indicator_calculations(self, data):
        ema(data, 5)
        ema(data, 20)
        ema(data, 40)
        atr(data)
        keltner_channel(data, shift=2)
        return data

    def buy_signal(self, data):
        data['Signal'] = np.where(
            ((data['Keltner_Bottom'] > data['Close'])
            &(data['Keltner_Bottom'] < data['Open']))
            , True, False)
        data['Buy Price'] = data['Close']
        return data

    def sell_signal(self, data):
        data['Sell'] = np.where(
            (data['Close'] > data['5-EMA'])
            , True, False)
        return data

    def stop_profit_loss(self, data):
        data['Stop Profit'] = data['5-EMA']
        data['Stop Loss'] = data['Buy Price'] - data['20-ATR'] * 2
        return data


