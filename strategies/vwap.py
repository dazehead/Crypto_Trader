import numpy as np
import pandas as pd
from strategies.strategy import Strategy

class Vwap_Strategy(Strategy):
    def __init__(self, df, **kwargs):
        super().__init__(df, **kwargs)
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

    # def calculate_long_vwap(self, window=100):
    #     typical_price = (self.high + self.low + self.close) / 3
    #     self.df['cum_price_volume'] = np.cumsum(typical_price * self.volume)
    #     self.df['cum_volume'] = np.cumsum(self.volume)
    #     long_vwap_values = self.df['cum_price_volume'].rolling(window=window).mean() / self.df['cum_volume'].rolling(window=window).mean()

    #     return long_vwap_values

    def custom_indicator(self, close ,volume_window=20):
        """for these signals we may not to to use generate signals because we want True all while its over vwap"""

        # Calculate indicators
        self.vwap_values = self.calculate_vwap()
        self.ti_data = pd.Series(self.vwap_values, index=self.close.index)
        #print(self.ti_data)

        # self.long_vwap_values = self.calculate_long_vwap()
        # self.ti2_data = pd.Series(self.long_vwap_values, index=self.close.index)

        # Calculate moving average of volume for volume confirmation
        volume_avg = self.volume.rolling(window=volume_window).mean()
        self.ti2_data = pd.Series(volume_avg, index=self.close.index)

        # Generate a buy signal based on the following conditions:
        # 1. The current closing price is above the current VWAP (self.vwap_values).
        # 2. The previous closing price was below or equal to the previous VWAP (using np.roll to access the previous values).
        # 3. The current volume is higher than the average volume (volume_avg).
        # All these conditions must be true to generate a buy signal.
        buy_signal = (self.close > self.vwap_values) & \
                    (self.volume > volume_avg)# & \
                    #(np.roll(self.close, 1) <= np.roll(self.vwap_values, 1))

        # Generate a sell signal based on the following conditions:
        # 1. The current closing price is below the current VWAP (self.vwap_values).
        # 2. The previous closing price was above or equal to the previous VWAP (using np.roll to access the previous values).
        # 3. The current volume is higher than the average volume (volume_avg).
        # All these conditions must be true to generate a sell signal.
        sell_signal = (self.close < self.vwap_values) & \
                    (self.volume > volume_avg)# & \
                    #(np.roll(self.close, 1) >= np.roll(self.vwap_values, 1))

        print(buy_signal.head(20))
        print('--------------------------------------------')
        print(sell_signal.head(20))
        

        signals = self.generate_signals(buy_signal, sell_signal, with_formating=False) 

        return signals
    