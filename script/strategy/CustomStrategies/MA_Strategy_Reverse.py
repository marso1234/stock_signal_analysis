import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import MACD, ema, atr, keltner_channel
from strategy.CustomStrategiesFunction.CustomStrategyUtils import MA_phase
class Strategy_MA_Reverse(Strategy):
    strategy_name = 'MA Strategy Reverse'
    indicator_config={'5-EMA':'red','20-EMA':'yellow','40-EMA':'blue','Keltner_Bottom':'black','Keltner_Upper':'black'}

    def __init__(self, symbol_list='NASDAQ', update_new=False, period='2y'):
        super().__init__(symbol_list, update_new, period)
        self.timeframe = '1d'
        self.moving_stop_profit = True
        self.moving_stop_loss = False

    def indicator_calculations(self, data):
        ema(data, 5)
        ema(data, 20)
        ema(data, 40)
        MACD(data)
        atr(data)
        keltner_channel(data, shift=2)
        data['Phase'] = MA_phase(data)

        data['Low < Keltner_Bottom'] = np.where((data['Low'] < data['Keltner_Bottom']),True, False)
        data['Prev 5'] = data['Low < Keltner_Bottom'].rolling(5).apply(lambda x: any(x)).astype(bool)
        return data

    def buy_signal(self, data):
        data['Signal'] = np.where(
        ((data['Prev 5']) & 
        (data['Close'] > data['5-EMA']) & (data['Open'] < data['5-EMA']) & (data['Close'] < data['40-EMA']))
            , True, False)
        data['Buy Price'] = data['Close']
        return data

    def sell_signal(self, data):
        data['Sell'] = np.where(
            ((data['Close'] > data['Keltner_Upper']) | 
             ((data['5-EMA'].shift(1) > data['20-EMA'].shift(1)) & (data['5-EMA']<data['20-EMA'])))
            , True, False)
        return data

    def stop_profit_loss(self, data):
        data['Stop Profit'] = data['Keltner_Upper']
        data['Stop Loss'] = data['Keltner_Bottom']
        return data


