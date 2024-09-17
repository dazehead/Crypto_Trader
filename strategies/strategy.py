"""This needs to return signals"""
import vectorbt as vbt
import pandas as pd
import numpy as np

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, df, **kwargs):
        self.df = df
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.open = self.df['open']
        self.high = self.df['high']
        self.low = self.df['low']
        self.close = self.df['close']

        self.entries = None
        self.exits = None


    def custom_indicator(self, close,  fast_window, slow_window):
        #close = self.close.to_list()

        fast_ma = vbt.MA.run(close, fast_window)
        slow_ma = vbt.MA.run(close, slow_window)
        self.ti_data = fast_ma.ma
        self.ti2_data = slow_ma.ma

        self.entries = fast_ma.ma_crossed_above(slow_ma)
        self.exits = fast_ma.ma_crossed_below(slow_ma)

        signal =np.zeros_like(close)
        signal[self.entries] = 1.0
        signal[self.exits] = -1.0

        return signal

    def _process_signals(self):
        pass
        