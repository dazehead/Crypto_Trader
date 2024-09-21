"""This needs to return signals"""
import vectorbt as vbt
import pandas as pd
import numpy as np
from utils import format_signals

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

        signals =np.zeros_like(close)
        signals[self.entries] = 1.0
        signals[self.exits] = -1.0

        return signals

    def generate_signals(self, buy_signal, sell_signal):
        """Common method to generate and format buy/sell signals"""
        signals = np.zeros_like(self.close)
        signals[buy_signal] = 1.0
        signals[sell_signal] = -1.0

        signals = format_signals(signals)

        # For graphing
        self.entries = np.zeros_like(signals, dtype=bool)
        self.exits = np.zeros_like(signals, dtype=bool)

        self.entries[signals == 1] = True
        self.exits[signals == -1] = True

        self.entries = pd.Series(self.entries, index=self.close.index)
        self.exits = pd.Series(self.exits, index=self.close.index)

        return signals
    
    def _process_signals(self):
        pass
        