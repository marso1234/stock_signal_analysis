import os
import pandas as pd
import requests
import json
import logging
import yfinance as yf

DIR_CACHE_ROOT = 'cache/stock_data'
DIR_SYMBOL_ROOT = 'ouput/symbol'
os.makedirs(DIR_CACHE_ROOT,exist_ok=True)
os.makedirs(DIR_SYMBOL_ROOT,exist_ok=True)

def get_NASDAQ(update_new):
    if update_new:
        url = 'https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25&offset=0&exchange=NASDAQ&download=true'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}
        dataString = requests.get(url,headers=headers).content
        json_data = json.loads(dataString)['data']
        tickersRawData = pd.DataFrame(json_data['rows'],columns=json_data['headers'])
        tickersRawData.columns = tickersRawData.columns.str.capitalize()

        #Save tickers as csv
        file = f'{DIR_SYMBOL_ROOT}/NASDAQ.csv'
        tickersRawData.to_csv(file, index=False)
        return tickersRawData['Symbol'].to_list()
    else:
        try:
            tickers = pd.read_csv(f'{DIR_SYMBOL_ROOT}/NASDAQ.csv')['Symbol'].to_list()
            return tickers
        except:
            logging.warning("Ticker file not exist, download from web...")
            return get_NASDAQ(update_new=True)

def get_SP500(update_new):
    if update_new:
        # Ref: https://stackoverflow.com/a/75845569/
        url = 'https://en.m.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tickers = pd.read_html(url, attrs={'id': 'constituents'})[0]
        file = f'{DIR_SYMBOL_ROOT}/SP500.csv'
        tickers.to_csv(file, index=False)
        return tickers['Symbol'].to_list()
    else:
        try:
            tickers = pd.read_csv(f'{DIR_SYMBOL_ROOT}/SP500.csv')['Symbol'].to_list()
            return tickers
        except:
            logging.warning("Ticker file not exist, download from web...")
            return get_SP500(update_new=True)
    
class DataManager:

    def __init__(self, symbol_list, period, timeframe, update_new):
        self.period=period
        self.timeframe=timeframe
        self.update_new=update_new
        self.data = {}
        if symbol_list == 'NASDAQ':
            self.symbol = get_NASDAQ(update_new)
        elif symbol_list == 'SP500':
            self.symbol = get_SP500(update_new)
        else:
            self.symbol = symbol_list.split(" ")


    def get_data(self):
        download_queue = '' # A string to queue up all 
        print("Update new: ",self.update_new)
        for s in self.symbol: # Handle data to be fetched from cache
            try:
                s = s.replace('/','-')
                if not self.update_new and os.path.exists(f'{DIR_CACHE_ROOT}/{s}_{self.timeframe}.csv'):
                    self.data[s] = pd.read_csv(f'{DIR_CACHE_ROOT}/{s}_{self.timeframe}.csv',index_col=False)
                else:
                    download_queue+= f' {s}'
            except Exception as e:
                pass
        if len(download_queue) != 0:
            symbol_queue = download_queue.split(' ')
            tickers = yf.Tickers(download_queue)
            for i, s in enumerate(symbol_queue): # Handle data that needs to be download online
                print(f'{i + 1}/{len(symbol_queue)}')
                try:
                    self.data[s] = tickers.tickers[s].history(interval=self.timeframe, period=self.period)
                    self.data[s].reset_index(inplace=True)
                    if 'Datetime' in self.data[s].columns:
                        self.data[s].rename(columns={'Datetime': 'Date'}, inplace=True)
                    self.data[s].to_csv(f'{DIR_CACHE_ROOT}/{s}_{self.timeframe}.csv',index=True)
                except Exception as e:
                    print(e)
        return self
    
    def apply(self, column_name, to_call, params): #Apply manipulation on dataframes using the provided function
        for key, value in self.data.items():
            self.data[key][column_name] = to_call(value[params])
    
    #Compare to apply, apply cover take the whole dataframe to to_call and assign a new dataframe
    #This could be inefficient if the operation is tiny
    def apply_cover(self, to_call):
        for key, value in self.data.items():
            self.data[key] = to_call(value)

    def get_latest(self, real_time_delay=True):
        temp = {}
        for s in self.symbol:
            if real_time_delay:
                try:
                    temp[s] = self.data[s].iloc[-2] # Prevent Realtime Data
                except:
                    temp[s] = self.data[s].iloc[-1] # May include real time data
            else:
                temp[s] = self.data[s].iloc[-1] # May include real time data
        return temp