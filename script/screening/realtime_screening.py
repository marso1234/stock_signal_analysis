import __init__
from data.DataManager import get_SP500
from strategy.CustomStrategies.MA_Strategy_adjustment_short import Strategy_MA_adjust_short
import math
from win10toast import ToastNotifier

#Config
real_time_delay=True
symbol_ls = get_SP500(update_new=False)
strategy_type = Strategy_MA_adjust_short

#Initialize
strategy = strategy_type(symbol_list=symbol_ls, update_new=True, period='5d')
strategy.fetch_data()
strategy.analyze()
data = strategy.get_latest(real_time_delay)
toaster = ToastNotifier()

#Loop to get data
for key, value in data.items():
    if value['Signal']:
        print(f'Time: {value["Date"]}')
        print(f'Symbol: {key}')
        print(f'Amount: {math.ceil(6480/ 5/ value["Buy Price"])}') #
        print(f'Buy Price: {value["Buy Price"]}')
        print(f'Stop Profit: {value["Stop Profit"]}')
        print(f'Stop Loss: {value["Stop Loss"]}')