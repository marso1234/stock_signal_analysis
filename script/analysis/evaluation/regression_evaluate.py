import __init__
from analysis.evaluation.regression_load_model import load_model_regression
import tensorflow as tf
import yfinance as yf
import numpy as np
from analysis.preprocess.feature_extract_per_stock import feature_extract
import plotly.graph_objects as go
import pandas as pd

#print(tf.__version__)

symbol = "GOOG"
period = 'max'
interval = '1d'
model = load_model_regression()

def run_evaluation(symbol, period='max', interval = '1d', plot=False, verbose=False):
    history = yf.download(symbol, period=period, interval=interval)

    print(history)
    feature_df = feature_extract(history.copy())
    
    feature_array = feature_df[-60:].to_numpy()

    # Relative PCT Calculation (includes Adjusted CLose)
    base_price = (feature_array[0,1] + feature_array[0,2])/2
    feature_array[:,0:4] = (feature_array[:,0:4] - base_price)/ (base_price + 0.00001)
    decoder_input = feature_array[-20:,:]

    feature_array = np.expand_dims(feature_array,axis=0)
    decoder_input = np.expand_dims(decoder_input,axis=0)

    result = model.predict([feature_array, decoder_input], verbose=verbose)
    print(result)
    result = base_price * (1+result)

    result = np.round(result, 2)
    if verbose:
        print(history.tail())
        print("Predicted High: ",max(result[0,:,0]))
        print("Predicted Low: ",min(result[0,:,1]))

    ticker_last = history[['Open','High', 'Low','Close']].iloc[-60:]
    len_last = len(ticker_last)
    # For Open and Close exist
    # # Append the result to the next 20 rows
    ticker_last_20 = history[['Open', 'High', 'Low', 'Close']].iloc[-20:]
    # combined_df = pd.concat([ticker_last_20.reset_index(drop=True), result_df], axis=0).reset_index(drop=True)

    if plot:
        #Plot graph
        fig = go.Figure(data=[go.Candlestick(x=list(range(0, len_last)),
                                            open=ticker_last['Open'],
                                            high=ticker_last['High'],
                                            low=ticker_last['Low'],
                                            close=ticker_last['Close'])])
        print(result.shape)
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

    return ticker_last_20, result

if __name__ == "__main__":
    run_evaluation(symbol=symbol, period=period, interval=interval, plot=True, verbose=True)