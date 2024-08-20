import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import MACD, ema, atr, keltner_channel
from script.strategy.CustomStrategiesFunction.CustomStrategyUtils import MA_phase

#Compare to the original strategy, this strategy wait for adjustment first, then buy
class Strategy_MA_adjust(Strategy):
    strategy_name = 'MA Adjustment Strategy'
    indicator_config={'5-EMA':'red','20-EMA':'yellow','40-EMA':'blue','Keltner_Upper':'black'}

    def __init__(self, symbol_list='NASDAQ', update_new=False, period='2y'):
        super().__init__(symbol_list, update_new, period)
        self.timeframe = '1d'

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

        def check_cross(series):
            return series.any()
        window_size = 5
        data['previous_5_20_cross'] = data['5-EMA'].shift(1) > data['20-EMA'].shift(1)
        previous_cross = data['previous_5_20_cross'].rolling(
            window=window_size, min_periods=1)\
            .apply(lambda x: check_cross(x), raw=False)
        data.drop(columns=['previous_5_20_cross'],inplace=True)

        previous_cross = np.where(previous_cross==1,True,False)
        yesterday_adjust = data['5-EMA'].shift(1) < data['20-EMA'].shift(1)
        today_cross = data['5-EMA'] > data['20-EMA']

        data['Signal'] = np.where(
            previous_cross & yesterday_adjust & today_cross
            , True, False)
        data['Buy Price'] = np.where(data['Signal'], data['Close'], np.nan)  # Adjusted to only set 'Buy Price' where 'Signal' is True
        return data

    def sell_signal(self, data):
        data['Sell'] = np.where(
            (data['Close'] > data['Keltner_Upper'])
            , True, False)
        return data

    def stop_profit_loss(self, data):
        data['Stop Profit'] = False#data['Buy Price'] + data['20-ATR'] * 4
        data['Stop Loss'] = data['Buy Price'] - data['20-ATR'] * 2
        return data
    