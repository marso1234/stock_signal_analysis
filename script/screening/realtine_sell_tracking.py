import __init__
from data.DataManager import get_SP500
from strategy.CustomStrategies.MA_Strategy_adjustment_short import Strategy_MA_adjust_short
import schedule
import time
import datetime
from win10toast import ToastNotifier

#Config
real_time_delay=True
symbol_ls = ['VST', 'OKE', 'RCL', 'VRTX', 'WMB']
strategy_type = Strategy_MA_adjust_short
toaster = ToastNotifier()

def check_sell():
    #Initialize
    strategy = strategy_type(symbol_list=symbol_ls, update_new=True, period='5d')
    strategy.fetch_data()
    strategy.analyze()
    data = strategy.get_latest(real_time_delay)
    to_sell = []

    #Loop to get data
    for key, value in data.items():
        print(value)
        if value['Sell']:
            print(f'Time: {value["Date"]}')
            print(f'Sell: {key}')
            to_sell.append(key)
    current_time = datetime.datetime.now()
    print(f"Cheking at: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if len(to_sell):
        toaster.show_toast(f"Sell Tracking Running", "Sell: {to_sell}", duration=10)
        print(f"Sell: {to_sell}")
    else:
        toaster.show_toast(f"Sell Tracking Running", "Nothing to sell", duration=10)
        print(f'Nothing to sell')

# Schedule the task
schedule.every().hour.at(":01").do(check_sell)
schedule.every().hour.at(":16").do(check_sell)
schedule.every().hour.at(":31").do(check_sell)
schedule.every().hour.at(":46").do(check_sell)

# Keep the script running
check_sell()
while True:
    schedule.run_pending()
    time.sleep(1)