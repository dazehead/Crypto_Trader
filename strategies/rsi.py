import talib
from strategies.strategy import Strategy

class RSI(Strategy):
    def __init__(self, df):
        super().__init__(df=df)

    def custom_indicator(self, close, rsi_window=None, buy_threshold=None, sell_threshold=None):

        rsi = self.calculate_rsi(close, rsi_window)
        self.osc1_data = ('RSI', rsi)

        buy_signal = rsi < buy_threshold
        sell_signal = rsi > sell_threshold

        signals = self.generate_signals(buy_signal, sell_signal)
        return signals        

    def calculate_rsi(self, close, rsi_window):
        rsi = talib.RSI(close, timeperiod=rsi_window)
        return rsi
