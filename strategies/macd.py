import talib as ta
from strategies.strategy import Strategy

class MACD(Strategy):
    def __init__(self, dict_df):
        super().__init__(dict_df=dict_df)

    def custom_indicator(self, fast_period=12, slow_period=26, signal_period=9):
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

        signals = self.generate_signals(buy_signal, sell_signal)

        return signals

    def calculate_macd(self, fastperiod, slowperiod, signalperiod):
        # Calculate MACD, signal line and MACD histogram
        macd, macd_signal, _ = ta.MACD(self.close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return macd, macd_signal