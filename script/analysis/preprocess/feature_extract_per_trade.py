
import __init__
import yfinance as yf
from data.DataManager import get_SP500
from indicators.CommonIndicators import atr
from strategy.CustomStrategies.MA_Strategy import Strategy_MA
import os
from backtest.Backtest import Backtest
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

symbol_ls = get_SP500(False)

DIR_ANALYSIS_ROOT = 'ouput/analysis'
os.makedirs(DIR_ANALYSIS_ROOT,exist_ok=True)

period = '2y'
interval = '1d'
strategy = Strategy_MA
features_extract_standardize = ['Open','High','Low','Close','Volume']
features_extract_minmax = ['5-EMA','20-EMA','40-EMA','20-ATR']
features_extract_binary = ['Signal', 'Sell']
features_static = ['beta','marketCap']
features_future = ['Future Price']
time_series = 20

features_all = features_extract_standardize+features_extract_minmax+features_extract_binary+features_static+features_future

static_feature_result = []
to_remove = []
for i, symbol in enumerate(symbol_ls):
    print(f'{i+1}/{len(symbol_ls)} {symbol}')
    # Static features (pre)
    try:
        ticker = yf.Ticker(symbol)
        previous_close = ticker.info['previousClose']
        volume = ticker.info['averageVolume']
        beta = ticker.info['beta']
        market_cap = ticker.info['marketCap']
        static_feature_result.append([symbol, previous_close, volume, beta, market_cap])
    except Exception as e:
        print(e)
        to_remove.append(symbol)

for t in to_remove:
    symbol_ls.remove(t)
    
static_feature_df = pd.DataFrame(static_feature_result, columns=['Symbol','previousClose','averageVolume']+features_static)
static_feature_df[features_static] = StandardScaler().fit_transform(static_feature_df[features_static])
price_scaler = StandardScaler().fit(static_feature_df['previousClose'].to_numpy().reshape(-1,1))
volume_scaler = StandardScaler().fit(static_feature_df['averageVolume'].to_numpy().reshape(-1,1))

os.makedirs(f"{DIR_ANALYSIS_ROOT}/{strategy.strategy_name}/data",exist_ok=True)
bt = Backtest()
meta_record = []
for i, symbol in enumerate(symbol_ls):
    print(f'{i+1}/{len(symbol_ls)} {symbol}')
    # Non-static feature
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period,interval=interval)
    history.reset_index(inplace=True)
    if 'Datetime' in history.columns:
        history.rename(columns={'Datetime': 'Date'}, inplace=True)
    strategy_df = strategy().analyze_pipeline(history)
    strategy_df = strategy_df.dropna().reset_index()
    backtest_record = bt.simulate(df=strategy_df, verbose=False, allow_repeat=True)['record']

    # Iterate over all 'Buy Dates' in record
    for i, trade_record in backtest_record.iterrows():
        # Find indices in strategy_df where 'Date' matches the current 'Buy Date'
        match_indices = strategy_df.index[strategy_df['Date'] == trade_record['Buy Date']].tolist()
        
        # For each matching index, select the N rows preceding the match
        for match_index in match_indices:
            if match_index - time_series < 0:  # Ensure start_index is not negative
                continue
            if match_index + time_series + 1 > len(strategy_df):
                break
            start_index = match_index - time_series 
            end_index = match_index
            future_index = match_index + time_series
            
            # Slice the record
            base_row = strategy_df.iloc[end_index]
            trimmed_record = strategy_df.iloc[start_index:end_index]
            
            #Preprocessing (Relative Percentage Change, Binary Encoding, Static Features apply)
            for f in features_extract_standardize:
                trimmed_record[f] = price_scaler.transform(trimmed_record[f].to_numpy().reshape(-1,1))
                if f=='Volume':
                    trimmed_record[f] = volume_scaler.transform(trimmed_record[f].to_numpy().reshape(-1,1))

            trimmed_record.loc[:, features_extract_minmax] = MinMaxScaler().fit_transform(trimmed_record.loc[:, features_extract_minmax])
            trimmed_record.loc[:,features_extract_binary] = trimmed_record[features_extract_binary].astype(int)
            
            # Merging features as one sample
            # Static Features (post), only be able to calcuate after computing the backtest
            trimmed_record.loc[:, features_static] = np.repeat(static_feature_df.loc[static_feature_df['Symbol'] == symbol, features_static].values, len(trimmed_record), axis=0)

            #trimmed_record['Future Price'] = (strategy_df.loc[end_index+1:future_index, 'Close'].values - base_row['Close']) / base_row['Close']
            trimmed_record['Future Price'] = price_scaler.transform(strategy_df['Close'].iloc[end_index:future_index].to_numpy().reshape(-1,1))
            #Labels to train + Reduce to only features needed
            trimmed_record = trimmed_record[features_all]
            record_path = f"{DIR_ANALYSIS_ROOT}/{strategy.strategy_name}/data/{symbol}_{i}.csv"
            trimmed_record.to_csv(record_path, index=False)

            # Save meta
            meta_record.append([symbol, record_path, int(trade_record['Profit'])])
meta_df = pd.DataFrame(meta_record, columns=['Symbol', 'Path', 'Label'])
meta_df.to_csv(f"{DIR_ANALYSIS_ROOT}/{strategy.strategy_name}/meta.csv",index=False)