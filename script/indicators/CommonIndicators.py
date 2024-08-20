

def ema(df,period):
    df["{period}-EMA".format(period=period)]=df["Close"].ewm(span=period, min_periods=period).mean()

def MACD(df,factor_1=12, factor_2=26, signal_line=9):
    df["EMA1"]=df["Close"].ewm(span=factor_1, min_periods=factor_1).mean()
    df["EMA2"]=df["Close"].ewm(span=factor_2, min_periods=factor_2).mean()
    df["DIF_MACD"]=df["EMA1"]-df["EMA2"]
    df["DEM_MACD"]=df["DIF_MACD"].ewm(span=signal_line, min_periods=signal_line).mean()
    df['Histogram_MACD']=(df["DIF_MACD"]-df["DEM_MACD"])*2
    df.drop(columns=["EMA1","EMA2"],inplace=True)

def atr(df, period=20): #Calculate ATR (Average True Range)
    #Find ATR for risk control
    df_size = df['Open'].size
    tr_ls = []
    tr_ls.append(None)#First Item
    for i in range(1, df_size):
        prev_c = df['Close'].iloc[i-1]
        curr_h = df['High'].iloc[i]
        curr_l = df['Low'].iloc[i]

        A = abs(curr_h - prev_c)
        B = abs(prev_c - curr_l)
        C = abs(curr_h - curr_l)
        
        tr = max(A,B,C)
        tr_ls.append(tr)
    df['TR'] = tr_ls
    df[f'{period}-ATR']= df["TR"].rolling(period,min_periods=period).mean()
    df.drop(columns=["TR"],inplace=True)

def keltner_channel(df,shift=2, period=10):
    clear_atr = False
    clear_ema = False
    if not f'{period}-ATR' in df.columns:
        atr(df, period)
        clear_atr = True
    if not f'{period}-EMA' in df.columns:  
        ema(df, period)
        clear_ema = True

    df['Keltner_Upper'] = df[f'{period}-EMA'] + shift * df[f'{period}-ATR']
    df['Keltner_Mid'] = df[f'{period}-EMA']
    df['Keltner_Bottom'] = df[f'{period}-EMA'] - shift * df[f'{period}-ATR']
    if clear_atr:
        df.drop(columns=[f'{period}-ATR'],inplace=True)
    if clear_ema:
        df.drop(columns=[f'{period}-EMA'],inplace=True)

def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
