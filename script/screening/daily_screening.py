import __init__
from data.DataManager import get_SP500
from strategy.CustomStrategies.MA_Strategy import Strategy_MA
import math
import pandas as pd
from datetime import datetime
import os

# Check the current working directory
print(f"Current working directory: {os.getcwd()}")


#Config
strategy_type = Strategy_MA

#Initialize
strategy = strategy_type(symbol_list='SP500', update_new=True, period='max')
strategy.fetch_data()
strategy.analyze()
data = strategy.get_latest(real_time_delay=False)
DIR_SIGNAL_ROOT = 'ouput/signal'
os.makedirs(DIR_SIGNAL_ROOT,exist_ok=True)

rows = []
#Loop to get data
for key, value in data.items():
    if value['Signal']:
            print(f'Signal in {key}')
            row = {
                'Time': value['Date'],
                'Symbol': key,
                'Amount': math.ceil(10000 / 7.8 / 5 / value['Buy Price'] * 10)/ 10,
                'Buy Price': value['Buy Price'],
                'Stop Profit': value['Stop Profit'],
                'Stop Loss': value['Stop Loss']
            }
            rows.append(row)

df = pd.DataFrame(rows)

# Get today's date and format it
today_date = datetime.today().strftime('%Y-%m-%d')

# Save the DataFrame to a CSV file with today's date in the filename
csv_file_path = os.path.join(DIR_SIGNAL_ROOT, f'signals_{today_date}.csv')
df.to_csv(csv_file_path, index=False)

# Open the CSV file
os.startfile(csv_file_path)