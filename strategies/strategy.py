"""This needs to return signals"""
import vectorbt as vbt
import pandas as pd

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, df, **kwargs):
        self.df = df
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.open = self.df['open'].tolist()
        self.high = self.df['high'].tolist()
        self.low = self.df['low'].tolist()
        self.close = self.df['close'].tolist()

        self.entries = None
        self.exits = None


    def custom_indicator(self, fast_window, slow_window):

        fast_ma = vbt.MA.run(self.close, fast_window)
        slow_ma = vbt.MA.run(self.close, slow_window)
        self.param1_data = fast_ma.ma
        self.param2_data = slow_ma.ma

        self.entries = fast_ma.ma_crossed_above(slow_ma)
        self.exits = fast_ma.ma_crossed_below(slow_ma)