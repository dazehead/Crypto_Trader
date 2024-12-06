import numpy as np
import pandas as pd
from core.strategies.strategy import Strategy

class Vwap(Strategy):
    def __init__(self, dict_df,risk_object = None, with_sizing=False):
        super().__init__(dict_df, risk_object=risk_object, with_sizing=with_sizing)
        self.vwap_values= None
        self.long_vwap_values = None

    def calculate_vwap(self):
        high = np.array(self.high)
        low = np.array(self.low)
        close = np.array(self.close)
        volume = np.array(self.volume)

        typical_price = (high + low + close) / 3

        cumulative_price_volume = np.cumsum(typical_price * volume)
        cumulative_volume = np.cumsum(volume)

        return cumulative_price_volume / cumulative_volume


    def custom_indicator(self, close=None ,volume_window=1):
        self.volume_window = volume_window
        """for these signals we may not to to use generate signals because we want True all while its over vwap"""

        # Calculate indicators
        self.vwap_values = self.calculate_vwap()
        self.ti1_data = ('VWAP', self.vwap_values)

        self.osc1_data = ('Volume', self.volume)

        buy_signal = (self.close > self.vwap_values)
        sell_signal = (self.close < self.vwap_values)   

        self.signals = self.generate_signals(buy_signal, sell_signal, with_formating=False) 

        return self.signals
    