import talib
from strategies.strategy import Strategy

class ATR(Strategy):
    def __init__(self, df, atr_window=14, **kwargs):
        super().__init__(df=df, **kwargs)
        self.atr_window = atr_window

    def custom_indicator(self, high, low, close, atr_window=None):
        atr_window = atr_window if atr_window is not None else self.atr_window

        atr = self.calculate_atr(high, low, close, atr_window)
        return atr

    def calculate_atr(self, high, low, close, atr_window):
        atr = talib.ATR(high, low, close, timeperiod=atr_window)
        return atr
