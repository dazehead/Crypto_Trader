import talib as ta
import numpy as np
import pandas as pd
from strategies.single.efratio import EFratio


class Kama(EFratio):
    def __init__(self, dict_df):
        super().__init__(dict_df=dict_df,)

    def custom_indicator(self,close=None, fast_window=2, slow_window=30, efratio_window=15):
        self.efratio_window = efratio_window
        self.efratios = self.calculate_efratios(self.efratio_window)
        self.osc1_data = ("Effiecency Ratio", self.efratios)

        self.fast_window = fast_window
        self.slow_window = slow_window
        
        self.kama = self.calculate_kama(self.fast_window, self.slow_window, self.efratio_window)
        self.kama = [np.nan if x == 0 else x for x in self.kama]
        self.ti1_data = ("KAMA", self.kama)        

        buy_signal = self.kama > self.close
        sell_signal = self.kama < self.close

        self.signals = self.generate_signals(buy_signal, sell_signal, with_formating=False)

        return self.signals


    def calculate_sc(self, fast_window=2, slow_window=30):

        """Calculate smoothing constants (SC) based on efficiency ratios."""
        fastest_SC = 2 / (fast_window + 1)
        slowest_SC = 2 / (slow_window + 1)
        
        sc = []
        for er in self.efratios:
            sc_value = (er * (fastest_SC - slowest_SC) + slowest_SC) ** 2
            sc.append(sc_value)
        return sc

    def calculate_kama(self, fast_window=2, slow_window=30, efratio_window=10):
        """Calculate Kaufman's Adaptive Moving Average (KAMA)."""
        sc = self.calculate_sc(fast_window, slow_window)
        close = self.close
        kama = []
        
        # Start index for valid KAMA calculation
        start_index = efratio_window - 1
        kama_length = len(close)
        
        # Initialize KAMA with zeros up to start_index
        for _ in range(start_index):
            kama.append(0)
        
        # Initial KAMA value is the price at start_index - 1
        initial_kama = close[start_index - 1]
        kama.append(initial_kama)
        
        # Calculate KAMA from start_index onwards
        for i in range(start_index + 1, kama_length):
            sc_i = sc[i]
            kama_prev = kama[i - 1]
            price_i = close[i]
            kama_i = kama_prev + sc_i * (price_i - kama_prev)
            kama.append(kama_i)
        
        return kama