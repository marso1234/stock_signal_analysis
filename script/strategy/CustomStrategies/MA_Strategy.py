import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import MACD, ema, atr, keltner_channel
from strategy.CustomStrategiesFunction.CustomStrategyUtils import MA_phase
class Strategy_MA(Strategy):
    strategy_name = 'MA Strategy'
    indicator_config={'5-EMA':'red','20-EMA':'yellow','40-EMA':'blue'}

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
        data['5-20 DIFF'] = data['5-EMA'] - data['20-EMA']
        data['20-40 DIFF'] = data['20-EMA'] - data['40-EMA']

        data['5_days_low'] = data['Low'].rolling(window=5+1).min()
        
        keltner_channel(data, shift=2)
        data['Phase'] = MA_phase(data)
        return data

    def buy_signal(self, data):
        data['Signal'] = np.where(
            (((data['Phase']==6) | (data['Phase']==1))
             & (data['5_days_low'] < data['Close']) # Prevent Stop loss instantly
             & (data['Keltner_Upper'] > data['Close']) # Prevent Stop Profit Triggers instantly
             & (data['20-EMA'] * 1.01 < data['Close'])
             & (data['5-20 DIFF'] > data['5-20 DIFF'].shift(1))
             & (data['20-40 DIFF'] > data['20-40 DIFF'].shift(1)))
            , True, False)
        data['Buy Price'] = data['Close']
        return data

    def sell_signal(self, data):
        data['Sell'] = np.where(
            (((data['Phase'] != 6) & (data['Phase'] != 1))
             & (data['5-20 DIFF'] < data['5-20 DIFF'].shift(1))
             & (data['5-20 DIFF'] < data['Close'] * 0.01) 
            )
            , True, False)
        # data['Sell'] = np.where(
        #     ((data['Phase']==1))
        #     , True, False)
        return data

    def stop_profit_loss(self, data):
        data['Stop Profit'] = data['Keltner_Upper']
        data['Stop Loss'] = data['5_days_low']
        return data


