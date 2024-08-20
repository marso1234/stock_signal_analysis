from backtest.Backtest import Backtest
from strategy.CustomStrategies.NR5 import Strategy_NR5
from strategy.CustomStrategies.MA_Strategy import Strategy_MA
from strategy.CustomStrategies.MA_Strategy_adjustment import Strategy_MA_adjust
from strategy.CustomStrategies.MA_Strategy_short import Strategy_MA_short
from strategy.CustomStrategies.MA_Strategy_adjustment_short import Strategy_MA_adjust_short

stock_symbol = "SP500"
strategy = Strategy_MA

BT = Backtest(strategy,update_new=False,symbol_list=stock_symbol)
BT.load_data()
#BT.analyze_stat(BT.simulate(stock_symbol,verbose=True),graph=True,indicators=strategy.indicator_config)
BT.analyze_all(verbose=False)