from strategies.strategy import Strategy
import numpy as np
import pandas as pd
import utils

class RSI_ADX_GPU(Strategy):
    def __init__(self, dict_df, risk_object=None, with_sizing=True, hyper=True):
        if __file__.endswith("rsi_adx_np.py"):
            self.is_numpy = True
        else:
            self.is_numpy = False
        super().__init__(dict_df=dict_df, risk_object=risk_object, with_sizing=with_sizing)
        self.hyper = hyper

    def custom_indicator(self, close=None, rsi_window=20, buy_threshold=15, sell_threshold=70,
                         adx_buy_threshold=30, adx_time_period=20):
        if not self.hyper:
            self.rsi_window = rsi_window
            self.buy_threshold = buy_threshold
            self.sell_threshold = sell_threshold
            self.adx_buy_threshold = adx_buy_threshold
            self.adx_time_period = adx_time_period

        # Calculate RSI
        rsi = self.calculate_rsi(self.close, rsi_window)
        rsi_np = np.pad(rsi, (len(self.close) - len(rsi), 0), constant_values=np.nan)  # Align dimensions

        # Generate RSI Signals
        buy_signal = rsi_np < buy_threshold
        sell_signal = rsi_np > sell_threshold

        signals = np.zeros_like(self.close, dtype=int)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        # Format signals
        signals = utils.format_signals(signals)

        # Calculate ADX
        adx = self.calculate_adx(self.high, self.low, self.close, adx_time_period)
        adx_np = np.pad(adx, (len(self.close) - len(adx), 0), constant_values=np.nan)  # Align dimensions

        # Generate ADX signals
        buy_signal_adx = adx_np > adx_buy_threshold
        sell_signal_adx = ~buy_signal_adx

        signals_adx = np.zeros_like(self.close, dtype=int)
        signals_adx[buy_signal_adx] = 1
        signals_adx[sell_signal_adx] = -1

        # Combine RSI and ADX signals
        final_signals = self.combine_signals(signals, signals_adx)
        final_signals = utils.format_signals(final_signals)

        if self.with_sizing:
            percent_to_size = self.risk_object.percent_to_size
            close_array = self.close.to_numpy(dtype=np.float64)
            final_signals = utils.calculate_with_sizing_numba(final_signals, close_array, percent_to_size)

        if not self.hyper:
            self.osc1_data = ('RSI', rsi_np)
            self.osc2_data = ('ADX', adx_np)
            self.signals = final_signals
            self.entries = pd.Series(self.signals == 1, index=self.close.index)
            self.exits = pd.Series(self.signals == -1, index=self.close.index)

        return final_signals

    def calculate_rsi(self, close, rsi_window):
        close = np.array(close)
        delta = np.diff(close, prepend=close[0])
        gain = np.maximum(delta, 0)
        loss = -np.minimum(delta, 0)

        avg_gain = np.convolve(gain, np.ones(rsi_window) / rsi_window, mode='valid')
        avg_loss = np.convolve(loss, np.ones(rsi_window) / rsi_window, mode='valid')

        rs = np.divide(avg_gain, avg_loss, out=np.zeros_like(avg_gain), where=avg_loss != 0)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_adx(self, high, low, close, adx_time_period):
        tr1 = np.abs(high[1:] - low[1:])
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))

        plus_dm = np.maximum(high[1:] - high[:-1], 0)
        minus_dm = np.maximum(low[:-1] - low[1:], 0)

        plus_dm = np.where(plus_dm > minus_dm, plus_dm, 0)
        minus_dm = np.where(minus_dm > plus_dm, minus_dm, 0)

        atr = np.convolve(true_range, np.ones(adx_time_period) / adx_time_period, mode='valid')
        plus_di = 100 * np.convolve(plus_dm, np.ones(adx_time_period) / adx_time_period, mode='valid') / atr
        minus_di = 100 * np.convolve(minus_dm, np.ones(adx_time_period) / adx_time_period, mode='valid') / atr

        dx = np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10) * 100
        adx = np.convolve(dx, np.ones(adx_time_period) / adx_time_period, mode='valid')
        return adx

    def combine_signals(self, *signals):
        signals_array = np.array(signals)
        combined_signals = np.zeros(signals_array.shape[1], dtype=int)
        combined_signals[np.all(signals_array == 1, axis=0)] = 1
        combined_signals[np.all(signals_array == -1, axis=0)] = -1
        return combined_signals
