import talib
from strategies.strategy import Strategy

class ATR(Strategy):
    def __init__(self, dict_df):
        super().__init__(dict_df=dict_df)

    def custom_indicator(self,atr_window=40):
        self.atr_window = atr_window

        atr = self.calculate_atr(atr_window)
        self.osc1_data = ('ATR', atr)
        return atr

    def calculate_atr(self, atr_window):
        atr = talib.ATR(self.high, self.low, self.close, timeperiod=atr_window)
        return atr
