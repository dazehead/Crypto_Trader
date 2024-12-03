import talib as ta
from strategies.strategy import Strategy

class RSI(Strategy):
    def __init__(self, dict_df,risk_object=None, with_sizing=False):
        super().__init__(dict_df=dict_df, risk_object=risk_object, with_sizing=with_sizing)

    def custom_indicator(self, close=None, rsi_window=10, buy_threshold=30, sell_threshold=80):

        self.rsi_window = rsi_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

        rsi = self.calculate_rsi(self.close, rsi_window)
        self.osc1_data = ('RSI', rsi)

        buy_signal = rsi < buy_threshold
        sell_signal = rsi > sell_threshold

        self.signals = self.generate_signals(buy_signal, sell_signal)

        return self.signals        

    def calculate_rsi(self, close, rsi_window):
        rsi = ta.RSI(close, timeperiod=rsi_window)
        return rsi
