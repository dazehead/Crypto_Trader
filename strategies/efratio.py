import numpy as np
import pandas as pd
import talib as ta
from strategies.strategy import Strategy


class EFratio_Strategy(Strategy):
    """Kuafman Efficiency Ratio Strategy"""
    def __init__(self, df, **kwargs):
        super().__init__(df = df, **kwargs)

    def custom_indicator(self, close, efratio_window=15, ef_threshold_buy=0.4, ef_threshold_sell=-0.8):

        efratios = self.calculate_efratios(efratio_window)

        # for trading
        buy_signal = efratios > ef_threshold_buy
        sell_signal = efratios < ef_threshold_sell

        signals = self.generate_signals(buy_signal, sell_signal)

        return signals
 
    
    def calculate_efratios(self, efratio_window):
        efratios = []
        close = self.close
        for i in range(len(close) - efratio_window + 1):
            window_prices = close[i:i + efratio_window]
            window_efratio = self._efratio(list(window_prices))
            efratios.append(window_efratio)
        
        zeros = np.zeros(efratio_window-1)
        efratios = np.concatenate((zeros, efratios))
        efratios = pd.Series(efratios, index=close.index)
        
        return efratios
    
    def _efratio(self, prices):
        price_changes = [prices[i]-prices[i-1] for i in range(1, len(prices))]
        absolute_price_changes = [abs(change) for change in price_changes]
        net_price_change = prices[-1] - prices[0]
        sum_absolute_price_changes = sum(absolute_price_changes)
        if sum_absolute_price_changes == 0:
            return 0
        kaufman_ratio = net_price_change / sum_absolute_price_changes

        return round(kaufman_ratio, 3)