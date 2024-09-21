import numpy as np
from strategies.strategy import Strategy

class Vwap_Strategy(Strategy):
    def __init__(self, df, **kwargs):
        super().__init__(df, **kwargs)
        self.volume = self.df['volume']
        self.vwap_values = None

    def vwap(self):
        high = np.array(self.high)
        low = np.array(self.low)
        close = np.array(self.close)
        volume = np.array(self.volume)

        typical_price = (high + low + close) / 3

        cumulative_price_volume = np.cumsum(typical_price * volume)
        cumulative_volume = np.cumsum(volume)

        self.vwap_value = cumulative_price_volume / cumulative_volume

        print("VWAP:", self.vwap_value)

    def custom_indicator(self):

        if self.vwap_values is None:
            self.calculate_vwap()

        buy_signal = (self.close > self.vwap_values) & (np.roll(self.close, 1) <= np.roll(self.vwap_values, 1))
        sell_signal = (self.close < self.vwap_values) & (np.roll(self.close, 1) >= np.roll(self.vwap_values, 1))

        return self.generate_signals(buy_signal, sell_signal)   
    