
import __init__
import yfinance as yf
from data.DataManager import get_SP500
from indicators.CommonIndicators import atr, ema, rsi
from strategy.CustomStrategiesFunction.CustomStrategyUtils import pct_change_diff, n_days_high, cross, price_range
import os
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
from sklearn.model_selection import train_test_split

base_feature = ['Open', 'High','Low', 'Close']
DIR_ANALYSIS_ROOT = 'ouput/analysis'
os.makedirs(DIR_ANALYSIS_ROOT,exist_ok=True)

# Config to customize
period = '5y'
interval = '1d'

end_date = datetime.now()
start_date = end_date - timedelta(days=60)  # Fetch data for the past year

# Custom Param
pct_diff_feature = ['pct_diff_High', 'pct_diff_Low']
global_base = [f'global_{i}' for i in base_feature]
extra_feature = ['20-ATR','Range','RSI']
def feature_extract(df):
    """
    Model per symbol
        Features to use

        Open High Low Close Volume (Must use), do scaling

        Dividend, Stock Splits: Binary Encoding

        Crossing: 5-20,5-40,20-40

        Acceleration: Low, High, do scaling

        20-Days High/Low: High, Low (4 features)
    """
    df.drop(columns=['Adj Close'], inplace=True)
    ema(df, 5)
    ema(df, 20)
    ema(df, 40)

    cross(df, '5-EMA', '20-EMA')
    cross(df, '5-EMA', '40-EMA')
    cross(df, '20-EMA', '40-EMA')

    df['Continuous'] = df.index.to_series().diff() == pd.Timedelta(days=1)
    df['Continuous'] = np.where(df['Continuous'] != 0, 1, 0)

    df['Dividends'] = np.where(df['Dividends'] != 0, 1, 0) if 'Dividends' in df.columns else 0
    df['Stock Splits'] = np.where(df['Stock Splits'] != 0, 1, 0) if 'Stock Splits' in df.columns else 0

    #Extra features
    price_range(df)
    atr(df)
    rsi(df)

    pct_change_diff(df, "High")
    pct_change_diff(df, "Low")
    df[pct_diff_feature] = df[pct_diff_feature].replace([np.inf, -np.inf], 0)
    df.dropna(inplace=True)

    if len(df) == 0:
        return pd.DataFrame()

    scaler = RobustScaler()
    df[['Volume']] = scaler.fit_transform(df[['Volume']])
    df[global_base] = scaler.fit_transform(df[base_feature])
    df[pct_diff_feature] = scaler.fit_transform(df[pct_diff_feature])
    df[extra_feature] = scaler.fit_transform(df[extra_feature])

    n_days_high(df, "High", 20, True)
    n_days_high(df, "High", 20, False)
    n_days_high(df, "Low", 20, True)
    n_days_high(df, "Low", 20, False)

    df.dropna(inplace=True)
    df.drop(['5-EMA','20-EMA','40-EMA'], inplace=True, axis=1)

    return df

def fetch_data_in_chunks(symbol, start_date, end_date, interval):
    data = pd.DataFrame()
    current_date = start_date
    while current_date < end_date:
        next_date = min(current_date + timedelta(days=60), end_date)
        chunk = yf.download(symbol, start=current_date, end=next_date, interval=interval)
        data = pd.concat([data, chunk])
        current_date = next_date
    return data

if __name__ == "__main__":
    postfix = '_transformer'
    os.makedirs(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/data",exist_ok=True)
    symbol_ls = get_SP500(False)
    rows_to_train = 60
    rows_to_predict = 60
    train_record = []
    test_record = []
    for i, symbol in enumerate(symbol_ls):
        print(f'{i+1}/{len(symbol_ls)} - {symbol}')
        symbol = symbol.replace('.','-')
        history = yf.download(symbol, period=period, interval=interval)#fetch_data_in_chunks(symbol, start_date, end_date, interval)
        feature_df = feature_extract(history)
        if len(feature_df) < (rows_to_train + rows_to_predict):
            print("Not enough data")
            continue
        feature_df.to_csv(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/data/{symbol}.csv",index=False)
        # Split the data based on time
        split_point = int(len(feature_df) * 0.8)
        # train_record.append([symbol, 0, split_point])
        # test_record.append([symbol, split_point, len(feature_df)])
        for k in range(rows_to_train, len(feature_df) - rows_to_predict):
            if k < split_point:
                train_record.append([symbol, k])
            else:
                test_record.append([symbol, k])


    # Create DataFrames for train and test records
    # train_record_df = pd.DataFrame(train_record, columns=["Symbol", "Available Start Index", "Available End Index"])
    # test_record_df = pd.DataFrame(test_record, columns=["Symbol", "Available Start Index", "Available End Index"])
    train_record_df = pd.DataFrame(train_record, columns=["Symbol", "Index"])
    test_record_df = pd.DataFrame(test_record, columns=["Symbol", "Index"])
    

    # Save the metadata
    train_record_df.to_csv(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/train_meta.csv", index=False)
    test_record_df.to_csv(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/test_meta.csv", index=False)