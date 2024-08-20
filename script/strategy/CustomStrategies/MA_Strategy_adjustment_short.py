import __init__
from Strategy import Strategy
import numpy as np
from indicators.CommonIndicators import MACD, ema, atr, keltner_channel
from script.strategy.CustomStrategiesFunction.CustomStrategyUtils import MA_phase

#Compare to the original strategy, this strategy wait for adjustment first, then buy
class Strategy_MA_adjust_short(Strategy):
    strategy_name = 'MA Adjustment Strategy short'
    indicator_config={'5-EMA':'red','20-EMA':'yellow','40-EMA':'blue','Keltner_Upper':'black'}
    
    def __init__(self, symbol_list='NASDAQ', update_new=False, period='5d'):
        super().__init__(symbol_list, update_new, period)
        self.timeframe = '5m'

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
            return series.sum()
        window_size = 5
        
        #Check If any time (in 5 days) do 5-EMA higher than 20-EMA
        # data['previous_20_40_cross'] = data['20-EMA'].shift(1) > data['40-EMA'].shift(1)
        # previous_cross = data['previous_20_40_cross'].rolling(
        #     window=window_size, min_periods=1)\
        #     .apply(lambda x: check_cross(x), raw=False)
        
        # data.drop(columns=['previous_20_40_cross'],inplace=True)

        data['previous_5_20_gap'] = abs(data['5-EMA'].shift(1) - data['20-EMA'].shift(1))
        data['previous_5_20_gap_dim'] = data['previous_5_20_gap'] < data['previous_5_20_gap'].shift(1)
        previous_cross = data['previous_5_20_gap_dim'].rolling(
            window=window_size, min_periods=1)\
            .apply(lambda x: check_cross(x), raw=False)
        
        data['Range'] = abs(data['Close'] - data['Open'])

        data.drop(columns=['previous_5_20_gap','previous_5_20_gap_dim'],inplace=True)

        previous_cross = np.where(previous_cross>=2,True,False)
        higher_40ema = data['Close'] > data['40-EMA']
        today_cross = data['5-EMA'] > data['20-EMA']
        up_trend = data['Close'] > data['40-EMA']
        today_green = data['Close'] > data['Open']
        higher_range = data['Range'] > data['Range'].shift(1)
        below_keltner = data['Close'] < data['Keltner_Upper']

        data['Signal'] = np.where(
            previous_cross & up_trend & higher_40ema & today_cross & below_keltner & today_green & higher_range
            , True, False)
        data['Buy Price'] = np.where(data['Signal'], data['Close'], False)  # Only set 'Buy Price' where 'Signal' is True
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
    