import talib as ta
from core.strategies.strategy import Strategy

class MACD(Strategy):
    def __init__(self, dict_df, risk_object=None, with_sizing=False):
        super().__init__(dict_df=dict_df, risk_object=risk_object, with_sizing=with_sizing)

    def custom_indicator(self,close =None, fast_period=35, slow_period=70, signal_period=33):

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

        # Calculate MACD and signal line
        macd, macd_signal = self.calculate_macd(fast_period, slow_period, signal_period)
        self.osc1_data = ('MACD', macd)
        self.osc2_data = ('MACD Signal', macd_signal)

        # Generate buy and sell signals based on MACD crossover
        buy_signal = macd > macd_signal  # MACD crosses above signal line
        sell_signal = macd < macd_signal  # MACD crosses below signal line

        self.signals = self.generate_signals(buy_signal, sell_signal)

        return self.signals

    def calculate_macd(self, fastperiod, slowperiod, signalperiod):
        # Calculate MACD, signal line and MACD histogram
        macd, macd_signal, macdhist = ta.MACD(self.close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return macd, macd_signal