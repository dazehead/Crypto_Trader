import talib as ta
from strategies.strategy import Strategy

class MACD(Strategy):
    def __init__(self, df):
        super().__init__(df=df)

    def custom_indicator(self, close, fastperiod=12, slowperiod=26, signalperiod=9):
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

        
        macd, macd_signal = self.calculate_macd(fastperiod, slowperiod, signalperiod)
        self.osc1_data = ('MACD', macd)
        self.osc2_data = ('MACD Signal', macd_signal)

        buy_signal = macd > macd_signal  
        sell_signal = macd < macd_signal  

        signals = self.generate_signals(buy_signal, sell_signal)
        return signals

    def calculate_macd(self, fastperiod, slowperiod, signalperiod):
        
        macd, macd_signal, _ = ta.MACD(self.close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return macd, macd_signal