import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import MACD, ema, atr, keltner_channel
from script.strategy.CustomStrategiesFunction.CustomStrategyUtils import MA_phase
class Strategy_MA_short(Strategy):
    strategy_name = 'MA Strategy short'
    indicator_config={'5-EMA':'red','20-EMA':'yellow','40-EMA':'blue','Keltner_Upper':'black'}

    def __init__(self, symbol_list='NASDAQ', update_new=False, period='1mo'):
        super().__init__(symbol_list, update_new, period)
        self.timeframe = '15m'

    def indicator_calculations(self, data):
        ema(data, 5)
        ema(data, 20)
        ema(data, 40)
        MACD(data)
        atr(data)
        keltner_channel(data, shift=2)
        data['Phase'] = MA_phase(data)
        return data

    def buy_signal(self, data):
        data['Signal'] = np.where(
            ((data['Phase']==6))
            , True, False)
        data['Buy Price'] = data['Close']
        return data

    def sell_signal(self, data):
        data['Sell'] = np.where(
            (data['Close'] > data['Keltner_Upper']) | (data['Close'] < data['40-EMA'])
            , True, False)
        # data['Sell'] = np.where(
        #     ((data['Phase']==1))
        #     , True, False)
        return data

    def stop_profit_loss(self, data):
        data['Stop Profit'] = data['Buy Price'] + data['20-ATR'] * 4
        data['Stop Loss'] = data['Buy Price'] - data['20-ATR'] * 2
        return data


