import numpy as np
import pandas as pd
from strategies.strategy import Strategy

class Vwap_Strategy(Strategy):
    def __init__(self, df):
        super().__init__(df)
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


    def custom_indicator(self, close ,volume_window=20):
        """for these signals we may not to to use generate signals because we want True all while its over vwap"""

        # Calculate indicators
        self.vwap_values = self.calculate_vwap()
        self.ti1_data = ('VWAP', self.vwap_values)
        #print(self.ti_data)

        # Calculate moving average of volume for volume confirmation
        volume_avg = self.volume.rolling(window=volume_window).mean()
        self.osc1_data = ('Volume', volume_avg)

        buy_signal = (self.close > self.vwap_values)
        sell_signal = (self.close < self.vwap_values)   

        signals = self.generate_signals(buy_signal, sell_signal, with_formating=False) 

        return signals
    