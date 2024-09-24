import talib
from strategies.strategy import Strategy

class ATR(Strategy):
    def __init__(self, df):
        super().__init__(df=df)

    def custom_indicator(self,atr_window=None):

        atr = self.calculate_atr(atr_window)
        self.osc1_data = ('ATR', atr)
        return atr

    def calculate_atr(self, atr_window):
        atr = talib.ATR(self.high, self.low, self.close, timeperiod=atr_window)
        return atr
