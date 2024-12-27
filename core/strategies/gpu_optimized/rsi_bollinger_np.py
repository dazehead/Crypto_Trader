from core.strategies.strategy import Strategy
import numpy as np
import pandas as pd
import core.utils as utils

class BollingerBands_RSI(Strategy):
    def __init__(self, dict_df, risk_object=None, with_sizing=True, hyper=None):
        super().__init__(dict_df=dict_df, risk_object=risk_object, with_sizing=with_sizing)
        self.hyper = hyper

    def custom_indicator(self, close=None, bb_period=20, bb_dev=2, rsi_window=14, rsi_buy=30, rsi_sell=70):
        if not self.hyper:
            self.bb_period = bb_period
            self.bb_dev = bb_dev
            self.rsi_window = rsi_window
            self.rsi_buy = rsi_buy
            self.rsi_sell = rsi_sell

        # Bollinger Bands
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(self.close_np, bb_period, bb_dev)
        bb_buy_signal = self.close_np < lower_band
        bb_sell_signal = self.close_np > upper_band

        # RSI
        rsi = self.calculate_rsi(self.close_np, rsi_window)
        rsi_buy_signal = rsi < rsi_buy
        rsi_sell_signal = rsi > rsi_sell

        # Combine signals
        bb_signals = np.zeros_like(self.close_np, dtype=int)
        bb_signals[bb_buy_signal] = 1
        bb_signals[bb_sell_signal] = -1

        rsi_signals = np.zeros_like(self.close_np, dtype=int)
        rsi_signals[rsi_buy_signal] = 1
        rsi_signals[rsi_sell_signal] = -1

        final_signals = self.combine_signals(bb_signals, rsi_signals)
        final_signals = utils.format_signals(final_signals)

        if self.with_sizing:
            final_signals = utils.calculate_with_sizing_numba(final_signals, self.close_np, self.risk_object.percent_to_size)

        self.osc1_data = ('BollingerBands', upper_band, middle_band, lower_band)
        self.osc2_data = ('RSI', rsi)
        self.signals = final_signals

        return final_signals

    def calculate_bollinger_bands(self, close, period, dev):
        upper_band, middle_band, lower_band = ta.BBANDS(close, timeperiod=period, nbdevup=dev, nbdevdn=dev)
        return upper_band, middle_band, lower_band

    def calculate_rsi(self, close, window):
        delta = np.diff(close, prepend=close[0])
        gain = np.maximum(delta, 0)
        loss = np.abs(np.minimum(delta, 0))

        avg_gain = np.convolve(gain, np.ones(window) / window, mode='valid')
        avg_loss = np.convolve(loss, np.ones(window) / window, mode='valid')

        rs = np.where(avg_loss == 0, 0, avg_gain / avg_loss)
        rsi = 100 - (100 / (1 + rs))

        pad_length = close.shape[0] - rsi.shape[0]
        return np.concatenate([np.full(pad_length, np.nan), rsi])
