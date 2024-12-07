from core.strategies.strategy import Strategy
import cupy as cp
import numpy as np
import pandas as pd
import core.utils as utils

class RSI_ADX_GPU(Strategy):
    def __init__(self, dict_df, risk_object=None, with_sizing=True, hyper=True):
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
        rsi_np = np.asnumpy(rsi)
        # print(rsi_np[-5:])
        # print(len(rsi_np))

        # Generate RSI Signals
        buy_signal = rsi_np < buy_threshold
        sell_signal = rsi_np > sell_threshold

        #Create initial signals
        signals = np.zeros_like(self.close, dtype=int)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        signals = utils.format_signals(signals)

        # Calculate ADX
        adx = self.calculate_adx_gpu(self.high, self.low, self.close, adx_time_period)
        adx_np = np.asnumpy(adx)

        # Generate ADX signals
        buy_signal_adx = adx_np > adx_buy_threshold
        sell_signal_adx = ~buy_signal_adx

        # Create ADX signals
        signals_adx = np.zeros_like(self.close, dtype=int)
        signals_adx[buy_signal_adx] = 1
        signals_adx[sell_signal_adx] = -1

        # Combine RSI and ADX signals
        final_signals = self.combine_signals(signals, signals_adx)

        # Format signals to avoid double entries/exits
        final_signals = utils.format_signals(final_signals)


        if self.with_sizing:
            percent_to_size = self.risk_object.percent_to_size
            close_array = self.close.to_numpy(dtype=np.float64)
            signal_array = np.array(final_signals)
            final_signals = utils.calculate_with_sizing_numba(signal_array, close_array, percent_to_size)

        if not self.hyper:
            self.osc1_data = ('RSI', rsi_np)
            self.osc2_data = ('ADX', adx_np)
            self.signals = final_signals


            self.entries = np.zeros_like(self.signals, dtype=bool)
            self.exits = np.zeros_like(self.signals, dtype=bool)

            self.entries[self.signals == 1] = True
            self.exits[self.signals == -1] = True

            self.entries = pd.Series(self.entries, index=self.close.index)
            self.exits = pd.Series(self.exits, index=self.close.index)

        return final_signals


    def calculate_rsi(self, close, rsi_window):
        delta = close[1:] - close[:-1]
        gain = np.maximum(delta, 0)
        loss = np.maximum(-delta, 0)

        # Calculate rolling averages (simple moving average for RSI)
        avg_gain = np.convolve(gain, np.ones(rsi_window) / rsi_window, mode='valid')
        avg_loss = np.convolve(loss, np.ones(rsi_window) / rsi_window, mode='valid')
        rs = avg_gain / avg_loss

        rsi = 100 - (100/ (1 + rs))

        # Align output size
        pad_length = close.shape[0] - rsi.shape[0]
        print(close.shape)
        print(rsi.shape)
        print(pad_length)
        rsi = np.concatenate([np.full(pad_length, np.nan), rsi])
        return rsi
    
    def calculate_adx_gpu(self, high, low, close, adx_time_period):
        """
        Calculates the Average Directional Movement Index (ADX) using GPU acceleration.

        Parameters:
        - high (numpy.ndarray): An array of high prices.
        - low (numpy.ndarray): An array of low prices.
        - close (numpy.ndarray): An array of close prices.
        - adx_time_period (int): The time period for calculating the ADX.

        Returns:
        - numpy.ndarray: An array of ADX values. The length of the array is equal to the length of the input arrays minus the time period.
        """
        tr1 = np.abs(high[1:] - low[1:])
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))

        # Directional Movement
        plus_dm = np.maximum(high[1:] - high[:-1], 0)
        minus_dm = np.maximum(low[:-1] - low[1:], 0)

        plus_dm = np.where(plus_dm > minus_dm, plus_dm, 0)
        minus_dm = np.where(minus_dm > plus_dm, minus_dm, 0)

        # Smoothed averages
        atr = np.convolve(true_range, np.ones(adx_time_period) / adx_time_period, mode='valid')
        plus_di = 100 * np.convolve(plus_dm, np.ones(adx_time_period) / adx_time_period, mode='valid') / atr
        minus_di = 100 * np.convolve(minus_dm, np.ones(adx_time_period) / adx_time_period, mode='valid') / atr

        # ADX calculation
        dx = np.abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        adx = np.convolve(dx, np.ones(adx_time_period) / adx_time_period, mode='valid')

        # Align output size
        pad_length = high.shape[0] - adx.shape[0]
        adx = np.concatenate([np.full(pad_length, np.nan), adx])
        return adx


    def combine_signals(self, *signals):
        # Convert the list of signals to a 2D NumPy array
        signals_array = np.array(signals)  # Shape: (num_signals, signal_length)
        
        # Check where all signals are 1
        all_ones = np.all(signals_array == 1, axis=0)
        
        # Check where all signals are -1
        all_neg_ones = np.all(signals_array == -1, axis=0)
        
        # Initialize combined_signals with zeros
        combined_signals = np.zeros(signals_array.shape[1], dtype=int)
        
        # Set combined_signals to 1 where all signals are 1
        combined_signals[all_ones] = 1
        
        # Set combined_signals to -1 where all signals are -1
        combined_signals[all_neg_ones] = -1
        
        return combined_signals
    
    # def format_signals(self, signals):
    #     """
    #     Formats signals to avoid double buys or sells.
    #     Optimized using NumPy arrays with a loop.
    #     """
    #     # Ensure signals is a NumPy array
    #     signals = np.array(signals)
    #     formatted_signals = np.zeros_like(signals)
    #     in_position = False

    #     for i in range(len(signals)):
    #         if signals[i] == 1 and not in_position:
    #             formatted_signals[i] = 1
    #             in_position = True
    #         elif signals[i] == -1 and in_position:
    #             formatted_signals[i] = -1
    #             in_position = False
    #         # Else, no change; formatted_signals[i] remains 0
    #         # in_position remains the same

    #     return formatted_signals