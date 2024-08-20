import __init__
from abc import ABC, abstractmethod
from data.DataManager import DataManager
import logging
# Abstract class for strategy
class Strategy(ABC):

    def __init__(self, symbol_list, update_new, period):
        self.symbol_list = symbol_list
        self.update_new = update_new
        self.period = period
        self.data_fetch = False

    def fetch_data(self):
        self.data_manager = DataManager(
                symbol_list=self.symbol_list, 
                period=self.period, 
                timeframe=self.timeframe, 
                update_new=self.update_new)
        self.data_manager.get_data()
        self.data_fetch = True

    def analyze(self):
        if not self.data_fetch:
            logging.warning("data is not fetched before analyze. Nothing will be done")
            return
        self.data_manager.apply_cover(to_call=self.analyze_pipeline)

    def get_latest(self, real_time_delay=True):
        return self.data_manager.get_latest(real_time_delay)

    # A function to be passed into DataManager
    def analyze_pipeline(self, data):
        temp = self.indicator_calculations(data)
        temp = self.buy_signal(temp)
        temp = self.sell_signal(temp)
        temp = self.stop_profit_loss(temp)
        return temp

    @abstractmethod
    def indicator_calculations(self, data):
        pass

    @abstractmethod
    def buy_signal(self, data):
        pass

    @abstractmethod
    def sell_signal(self, data):
        pass

    @abstractmethod
    def stop_profit_loss(self, data):
        pass