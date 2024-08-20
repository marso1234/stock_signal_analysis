import numpy as np

def MA_phase(df):
    size = df['Date'].size

    result = []
    for i in range(size):
        EMA5 = df['5-EMA'].iloc[i]
        EMA20 = df['20-EMA'].iloc[i]
        EMA40 = df['40-EMA'].iloc[i]

        phase = -1

        if EMA5 > EMA20 and EMA20 > EMA40:
            phase = 1
        elif EMA20 > EMA5 and EMA5 > EMA40:
            phase = 2
        elif EMA20 > EMA40 and EMA40>EMA5:
            phase = 3
        elif EMA40 > EMA20 and EMA20 > EMA5:
            phase = 4
        elif EMA40 > EMA5 and EMA5 > EMA20:
            phase = 5
        elif EMA5 > EMA40 and EMA40 > EMA20:
            phase = 6
        result.append(phase)
    return result

def cross(df, col_1, col_2):
    df[f'cross-{col_1}-{col_2}'] = np.where(
        (df[col_1].shift(1) < df[col_2].shift(1)) & (df[col_1] > df[col_2]),
        1,
        np.where(
            (df[col_1].shift(1) > df[col_2].shift(1)) & (df[col_1] < df[col_2]),
            -1,
            0
        )
    )

def n_days_high(df, col, n, high=True):
    if high:
        df[f'{n}_days_high_{col}'] = np.where(
            df[col] == df[col].rolling(window=n+1).max(), 1, 0
        )
    else:
        df[f'{n}_days_low_{col}'] = np.where(
            df[col] == df[col].rolling(window=n+1).min(), 1, 0
        )

def pct_change_diff(df, col):

    pct_change = df[col].pct_change()
    # Rate of rate of change
    df[f'pct_diff_{col}'] = pct_change - pct_change.shift(1)

def price_range(df):
    df["Range"] = df['High'] - df['Low']
