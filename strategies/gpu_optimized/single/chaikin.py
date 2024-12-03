import talib as ta
from strategies.strategy import Strategy
import pandas as pd

class ADX(Strategy):
    def __init__(self, dict_df, with_sizing = False):
        super().__init__(dict_df=dict_df, with_sizing = with_sizing)

    def custom_indicator(self,close =None,buy_threshold= 50, time_period=14):

        self.signal_period = time_period
        self.buy_threshold = buy_threshold

        # Calculate 
        adx = self.calculate_adx(time_period)
        self.osc1_data = ('ADX', adx)

        buy_signal = adx > self.buy_threshold
        sell_signal = ~buy_signal # assigns opposite values of what buy_signal is

        self.signals = self.generate_signals(buy_signal, sell_signal, with_formating=False)

        return self.signals

    def calculate_adx(self, time_period):
        adx = ta.ADX(self.high, self.low, self.close, time_period)
        return adx