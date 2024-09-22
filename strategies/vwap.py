import numpy as np
import talib
from strategies.strategy import Strategy

class Vwap_Strategy(Strategy):
    def __init__(self, df, **kwargs):
        super().__init__(df, **kwargs)
        self.volume = self.df['volume']
        self.vwap_values = None

    def calculate_vwap(self):
        high = np.array(self.high)
        low = np.array(self.low)
        close = np.array(self.close)
        volume = np.array(self.volume)

        typical_price = (high + low + close) / 3

        cumulative_price_volume = np.cumsum(typical_price * volume)
        cumulative_volume = np.cumsum(volume)

        self.vwap_value = cumulative_price_volume / cumulative_volume

        print("VWAP:", self.vwap_value)

    def calculate_long_vwap(self, window=100):
        typical_price = (self.high + self.low + self.close) / 3
        self.df['cum_price_volume'] = np.cumsum(typical_price * self.volume)
        self.df['cum_volume'] = np.cumsum(self.volume)
        self.long_vwap_values = self.df['cum_price_volume'].rolling(window=window).mean() / self.df['cum_volume'].rolling(window=window).mean()

    def custom_indicator(self, rsi_period=14, atr_period=14, volume_window=20, threshold=0.001, ef_threshold_buy=30, ef_threshold_sell=70, atr_threshold=0.005):
        # Calculate indicators
        if self.vwap_values is None:
            self.calculate_vwap()

        if self.long_vwap_values is None:
            self.calculate_long_vwap()

        # Calculate RSI
        rsi = talib.RSI(self.close, timeperiod=rsi_period)
        
        # Calculate ATR for volatility filter
        atr = talib.ATR(self.high, self.low, self.close, timeperiod=atr_period)

        # Calculate moving average of volume for volume confirmation
        volume_avg = self.volume.rolling(window=volume_window).mean()

        # Buy signal: Price crosses above VWAP, RSI < 30, high ATR, price > long-term VWAP, and volume > average
        buy_signal = (self.close > self.vwap_values * (1 + threshold)) & \
                     (np.roll(self.close, 1) <= np.roll(self.vwap_values, 1) * (1 + threshold)) & \
                     (rsi < ef_threshold_buy) & \
                     (atr > atr_threshold) & \
                     (self.close > self.long_vwap_values) & \
                     (self.volume > volume_avg)

        # Sell signal: Price crosses below VWAP, RSI > 70, high ATR, price < long-term VWAP, and volume > average
        sell_signal = (self.close < self.vwap_values * (1 - threshold)) & \
                      (np.roll(self.close, 1) >= np.roll(self.vwap_values, 1) * (1 - threshold)) & \
                      (rsi > ef_threshold_sell) & \
                      (atr > atr_threshold) & \
                      (self.close < self.long_vwap_values) & \
                      (self.volume > volume_avg)

        return self.generate_signals(buy_signal, sell_signal) 
    