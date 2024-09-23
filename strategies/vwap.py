import numpy as np
import talib as ta
from strategies.strategy import Strategy

class Vwap_Strategy(Strategy):
    def __init__(self, df, **kwargs):
        super().__init__(df, **kwargs)
        self.volume = self.df['volume']
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
        #print("VWAP:", self.vwap_value)

        return cumulative_price_volume / cumulative_volume

    def calculate_long_vwap(self, window=100):
        typical_price = (self.high + self.low + self.close) / 3
        self.df['cum_price_volume'] = np.cumsum(typical_price * self.volume)
        self.df['cum_volume'] = np.cumsum(self.volume)
        long_vwap_values = self.df['cum_price_volume'].rolling(window=window).mean() / self.df['cum_volume'].rolling(window=window).mean()

        return long_vwap_values

    def custom_indicator(self,close, rsi_period=14, atr_period=14, volume_window=20):
        #assign variables
        threshold= 0.001
        rsi_threshold_buy = 40
        rsi_threshold_sell = 60
        atr_threshold = 0.005

        # Calculate indicators
        self.vwap_values = self.calculate_vwap()
        self.long_vwap_values = self.calculate_long_vwap()

        # Calculate RSI
        rsi = ta.RSI(self.close, timeperiod=rsi_period)
        
        # Calculate ATR for volatility filter
        atr = ta.ATR(self.high, self.low, self.close, timeperiod=atr_period)
        self.ti_data = atr

        # Calculate moving average of volume for volume confirmation
        volume_avg = self.volume.rolling(window=volume_window).mean()

        # Buy signal: Price crosses above VWAP, RSI < 30, high ATR, price > long-term VWAP, and volume > average
        buy_signal = (self.close > self.vwap_values * (1 + threshold)) & \
                     (np.roll(self.close, 1) <= np.roll(self.vwap_values, 1) * (1 + threshold)) & \
                     (rsi < rsi_threshold_buy) & \
                     (self.close > self.long_vwap_values) & \
                     (self.volume > volume_avg)
        print(buy_signal)

        # Sell signal: Price crosses below VWAP, RSI > 70, high ATR, price < long-term VWAP, and volume > average
        sell_signal = (self.close < self.vwap_values * (1 - threshold)) & \
                      (np.roll(self.close, 1) >= np.roll(self.vwap_values, 1) * (1 - threshold)) & \
                      (rsi > rsi_threshold_sell) & \
                      (atr > atr_threshold) & \
                      (self.close < self.long_vwap_values) & \
                      (self.volume > volume_avg)
        
        signals = self.generate_signals(buy_signal, sell_signal) 

        return signals
    