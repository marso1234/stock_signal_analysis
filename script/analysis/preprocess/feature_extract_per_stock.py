
import __init__
import yfinance as yf
from data.DataManager import get_SP500
from indicators.CommonIndicators import atr, ema, rsi
from strategy.CustomStrategiesFunction.CustomStrategyUtils import pct_change_diff, n_days_high, cross, price_range
import os
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
import pandas as pd
import numpy as np
import warnings

base_feature = ['Open', 'High','Low', 'Close', 'Volume']
DIR_ANALYSIS_ROOT = 'ouput/analysis'
os.makedirs(DIR_ANALYSIS_ROOT,exist_ok=True)

# Config to customize
period = 'max'
interval = '1d'
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
    ema(df, 5)
    ema(df, 20)
    ema(df, 40)

    cross(df, '5-EMA', '20-EMA')
    cross(df, '5-EMA', '40-EMA')
    cross(df, '20-EMA', '40-EMA')

    df['Dividends'] = np.where(df['Dividends'] != 0, 1, 0)
    df['Stock Splits'] = np.where(df['Stock Splits'] != 0, 1, 0)


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

    df[global_base] = RobustScaler().fit_transform(df[base_feature])
    df[pct_diff_feature] = RobustScaler().fit_transform(df[pct_diff_feature])
    df[extra_feature] = RobustScaler().fit_transform(df[extra_feature])

    n_days_high(df, "High", 20, True)
    n_days_high(df, "High", 20, False)
    n_days_high(df, "Low", 20, True)
    n_days_high(df, "Low", 20, False)

    df.dropna(inplace=True)
    df.drop(['5-EMA','20-EMA','40-EMA'], inplace=True, axis=1)

    return df


if __name__ == "__main__":
    postfix = '_transformer'
    os.makedirs(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/data",exist_ok=True)
    symbol_ls = get_SP500(False)
    rows_to_train = 100
    rows_to_predict = 20
    record = []
    for i, symbol in enumerate(symbol_ls):
        print(f'{i+1}/{len(symbol_ls)} - {symbol}')
        symbol = symbol.replace('.','-')
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period,interval=interval)
        feature_df = feature_extract(history)
        if len(feature_df) < (rows_to_train + rows_to_predict):
            print("Not enough data")
            continue
        feature_df.to_csv(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/data/{symbol}.csv",index=False)
        for k in range(rows_to_train, len(feature_df)-rows_to_predict):
            record.append([symbol, k])
    record_df = pd.DataFrame(record, columns=["Symbol","Index"])
    record_df.to_csv(f"{DIR_ANALYSIS_ROOT}/price_{period}_{interval}{postfix}/meta.csv",index=False)