import numpy as np
import pandas as pd
import talib as ta
from strategies.strategy import Strategy


class EFratio(Strategy):
    """Efficiency Ratio Strategy"""
    def __init__(self, dict_df, with_sizing=False):
        super().__init__(dict_df = dict_df, with_sizing=with_sizing)

    def custom_indicator(self, close=None, efratio_window=15, buy_threshold=0.4, sell_threshold=-0.8):
        self.efratio_window = efratio_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

        efratios = self.calculate_efratios(efratio_window)
        self.osc1_data = ("Effiecency Ratio", efratios)

        # for trading
        buy_signal = efratios > buy_threshold
        sell_signal = efratios < sell_threshold

        self.signals = self.generate_signals(buy_signal, sell_signal)

        return self.signals
 
    
    def calculate_efratios(self, efratio_window):
        """function that calculates efficiency ratio based on efratio_window"""
        efratios = []
        close = self.close
        for i in range(len(close) - efratio_window + 1):
            window_prices = close[i:i + efratio_window]
            window_efratio = self._efratio(list(window_prices))
            efratios.append(window_efratio)
        
        zeros = np.zeros(efratio_window-1)
        efratios = np.concatenate((zeros, efratios))
        
        return efratios
    
    def _efratio(self, prices):
        """helper function for efratio this code gets looped"""
        price_changes = [prices[i]-prices[i-1] for i in range(1, len(prices))]
        absolute_price_changes = [abs(change) for change in price_changes]
        net_price_change = prices[-1] - prices[0]
        sum_absolute_price_changes = sum(absolute_price_changes)
        if sum_absolute_price_changes == 0:
            return 0
        kaufman_ratio = net_price_change / sum_absolute_price_changes

        return round(kaufman_ratio, 3)