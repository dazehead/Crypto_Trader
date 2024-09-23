import talib
from strategies.strategy import Strategy

class RSI(Strategy):
    def __init__(self, df, close, rsi_window=14, buy_threshold=30, sell_threshold=70, **kwargs):
        super().__init__(df=df, close=close, **kwargs)
        self.rsi_window = rsi_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def custom_indicator(self, close, rsi_window=None, buy_threshold=None, sell_threshold=None):
        #dynamic parameters
        rsi_window = rsi_window if rsi_window is not None else self.rsi_window
        buy_threshold = buy_threshold if buy_threshold is not None else self.buy_threshold
        sell_threshold = sell_threshold if sell_threshold is not None else self.sell_threshold

        rsi = self.calculate_rsi(close, rsi_window)

        buy_signal = rsi < buy_threshold
        sell_signal = rsi > sell_threshold

        signals = self.generate_signals(buy_signal, sell_signal)
        return signals        

    def calculate_rsi(self, close, rsi_window):
        rsi = talib.RSI(close, timeperiod=rsi_window)
        return rsi
