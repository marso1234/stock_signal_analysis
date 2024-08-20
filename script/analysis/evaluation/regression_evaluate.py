import __init__
from regression_load_model import load_model_regression
import tensorflow as tf
import yfinance as yf
import numpy as np
from analysis.preprocess.feature_extract_per_stock import feature_extract
import plotly.graph_objects as go
import pandas as pd

#print(tf.__version__)

symbol = "APH"
period = 'max'
interval = '1d'

model = load_model_regression()
ticker = yf.Ticker(symbol)
history = ticker.history(period=period,interval=interval)

feature_df = feature_extract(history.copy())
print(history.tail())
feature_array = np.expand_dims(feature_df[-20:],axis=0)

# Relative PCT Calculation
base_ohlcv = np.array(feature_array[0,0,0:5])
feature_array[0,:,0:5] = (feature_array[0,:,0:5] - base_ohlcv)/ (base_ohlcv + 0.00001)

result = model.predict(feature_array)

# Only High and Low
result = base_ohlcv[1:3] * (1+result)
result = np.round(result, 2)

print("Predicted High: ",max(result[0,:,0]))
print("Predicted Low: ",min(result[0,:,1]))

ticker_last = history[['Open','High', 'Low','Close']].iloc[-60:]
len_last = len(ticker_last)
# For Open and Close exist
# # Append the result to the next 20 rows
# ticker_last_20 = history[['Open', 'High', 'Low', 'Close']].iloc[-20:]
# combined_df = pd.concat([ticker_last_20.reset_index(drop=True), result_df], axis=0).reset_index(drop=True)

#Plot graph
fig = go.Figure(data=[go.Candlestick(x=list(range(0, len_last)),
                                     open=ticker_last['Open'],
                                     high=ticker_last['High'],
                                     low=ticker_last['Low'],
                                     close=ticker_last['Close'])])
fig.add_trace(go.Scatter(x=list(range(len_last, len_last+20)), y=result[0,:,0], mode='lines', name='High'))
fig.add_trace(go.Scatter(x=list(range(len_last, len_last+20)), y=result[0,:,1], mode='lines', name='Low'))
fig.update_layout(title=f'Predict - {symbol}',
                    xaxis=dict(
                tickmode='auto',  # Automatically determine tick spacing
                nticks=20,  # Specify the maximum number of ticks to display
                type='category',  # Use if your x-axis data is categorical (dates as categories)
                title='Timestep',
                rangeslider_visible=True
                ),
                yaxis_title='Price')  # Hides the range slider at the bottom

fig.show()