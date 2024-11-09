"""This needs to return signals"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import plotly.subplots as sp
import plotly.graph_objects as go
import sys
import talib as ta

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, dict_df, risk_object=None, with_sizing=False):
        if not isinstance(dict_df, dict):
            print('You have passed a Dataframe. This Class needs to be dictionary with key as symbol and value as DataFrame')
            sys.exit(1)
        for key, value in dict_df.items():
            self.symbol = key
            self.df = value
        self.with_sizing = with_sizing
        self.risk_object = risk_object

        self.open = self.df['open']
        self.high = self.df['high']
        self.low = self.df['low']
        self.close = self.df['close']
        self.volume = self.df['volume']

        self.granularity = None
        self.set_granularity()

        self.entries = None
        self.exits = None

        # technical indicator data assigned in custom_indicator
        #
        self.ti1_data = None
        self.ti2_data = None
        self.ti3_data = None
        self.ti4_data = None

        # oscilator data assigned in custom_indicator
        self.osc1_data = None
        self.osc2_data = None
        self.osc3_data = None
        self.osc4_data = None

        self.buy_threshold = None
        self.sell_threshold = None

        self.portfolio = None


    def custom_indicator(self, close,  fast_window=5, slow_window=30):
        self.fast_window = fast_window
        self.slow_window = slow_window

        fast_ma = vbt.MA.run(close, fast_window)
        slow_ma = vbt.MA.run(close, slow_window)
        
        self.ti1_data = ("Fast MA", fast_ma.ma)
        self.ti2_data = ("Slow MA", slow_ma.ma)

        self.entries = fast_ma.ma_crossed_above(slow_ma)
        self.exits = fast_ma.ma_crossed_below(slow_ma)

        signals =np.zeros_like(close)
        signals[self.entries] = 1
        signals[self.exits] = -1
        self.signals = signals

        return self.signals

    def generate_signals(self, buy_signal, sell_signal, with_formating=True):
        """Common method to generate and format buy/sell signals"""
        signals = np.zeros_like(self.close, dtype=int)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        if with_formating:
            signals = self.format_signals(signals)
            # if self.with_sizing:
            #     signals = self.calculate_with_sizing(signals)##########################################################################

        # For graphing
        self.entries = np.zeros_like(signals, dtype=bool)
        self.exits = np.zeros_like(signals, dtype=bool)

        self.entries[signals == 1] = True
        self.exits[signals == -1] = True

        self.entries = pd.Series(self.entries, index=self.close.index)
        self.exits = pd.Series(self.exits, index=self.close.index)
        return signals
    
    def calculate_with_sizing(self, signals):
        #convert signals to pandas series
        date_with_signals = pd.DataFrame({'signal': signals,
                                          'close': self.close}, index=self.close.index)
        # Copy of the original DataFrame to avoid modifying it directly
        df = date_with_signals.copy()

        # Initialize variables to hold the saved close price and a flag to check if we are in a tracking phase
        saved_close = None
        tracking = False

        # Iterate through each row in the DataFrame
        for i in range(len(df)):
            # Check if the signal is 1 and we are not already tracking
            if df['signal'].iloc[i] == 1 and not tracking:
                # Save the close price and start tracking
                saved_close = df['close'].iloc[i]
                tracking = True

            # If tracking, compare each subsequent close price
            elif tracking:
                # Calculate the 2% threshold
                target_close = saved_close * (1 + self.risk_object.percent_to_size) # this value will be calculated through the risk class
                
                # Check if the close price has increased by 2% or more from the saved close price
                if df['close'].iloc[i] >= target_close and df['signal'].iloc[i] == 0:
                    # Update the signal to 1
                    df.at[df.index[i], 'signal'] = 1
                    saved_close = df['close'].iloc[i]
                
                if df['close'].iloc[i] <= (target_close * (1 - (self.risk_object.percent_to_size * 2))) and df['signal'].iloc[i] ==0:
                    saved_close = df['close'].iloc[i]
                
                # Stop tracking if a -1 signal is encountered
                if df['signal'].iloc[i] == -1:
                    tracking = False
                    saved_close = None  # Reset saved close
        signals = df['signal'].to_numpy()
        return signals

        
    
    def format_signals(self, signals):
        """formats signals so no double buy or double sells"""
        formatted_signals = np.zeros_like(signals)
        in_position = False
            
        for i in range(len(signals)):
            if signals[i] == 1 and not in_position:
                formatted_signals[i] = 1
                in_position = True
            elif signals[i] == -1 and in_position:
                formatted_signals[i] = -1
                in_position = False
        return formatted_signals    


    def combine_signals(self, *signals):
        combined_signals = []
        signal_length = len(signals[0])  # Assuming all signals have the same length
        try:
            for i in range(signal_length):
                # Get all the signals at the current index across the provided lists
                current_signals = [signal[i] for signal in signals]
                
                if all(s == 1 for s in current_signals):
                    combined = 1  # Set to 1 only if all signals are 1
                elif all(s == -1 for s in current_signals):
                    combined = -1  # Set to -1 only if all signals are -1
                else:
                    combined = 0  # Set to 0 if there's any mix of values
                combined_signals.append(combined)
        except Exception as e:
            print(f"Invalid signals: {e}")
        
        combined_signals = self.format_signals(combined_signals)
        if self.with_sizing:
            combined_signals = self.calculate_with_sizing(combined_signals)

        self.entries = np.zeros_like(self.close, dtype=bool) #from signal to signal_length
        self.exits = np.zeros_like(self.close, dtype=bool)#from signal to signal_length

        self.entries[combined_signals == 1] = True
        self.exits[combined_signals == -1] = True

        self.entries = pd.Series(self.entries, index=self.close.index)
        self.exits = pd.Series(self.exits, index=self.close.index)

        return combined_signals
          


    def graph(self):
 
        # Start by plotting the first figure (Close price)
        param_number = 0
        #fig1 = self.close.vbt.plot(trace_kwargs=dict(name='Close'))
        fig1 = go.Figure(data=[go.Candlestick(x=self.close.index,
                                             open=self.open,
                                             high=self.high,
                                             low=self.low,
                                             close=self.close)])

        fig2 = None
        osc_data = None

        # Loop over param_numbers to dynamically access ti_data and osc_data
        while True:
            param_number += 1

            # Dynamically access ti{i}_data and check if it's not None
            ti_data_attr = getattr(self, f"ti{param_number}_data", None)
            
            if ti_data_attr is not None:
                ti_data_name, ti_data = ti_data_attr  # Unpack the tuple (name, data)
                ti_data = pd.Series(ti_data, index=self.close.index)
                fig1 = ti_data.vbt.plot(trace_kwargs=dict(name=ti_data_name), fig=fig1)

            # Dynamically access osc{i}_data and check if it's not None
            osc_data_attr = getattr(self, f"osc{param_number}_data", None)
            
            if osc_data_attr is not None:
                osc_data_name, osc_data = osc_data_attr  # Unpack the tuple (name, data)
                osc_data = pd.Series(osc_data, index=self.close.index)
                if fig2 is None:
                    fig2 = osc_data.vbt.plot(trace_kwargs=dict(name=osc_data_name))
                else:
                    fig2 = osc_data.vbt.plot(trace_kwargs=dict(name=osc_data_name), fig=fig2)

            # Break the loop if both ti_data and osc_data for the current param_number are None
            if ti_data_attr is None and osc_data_attr is None:
                break

        # Plot entry and exit markers on the first figure (fig1)
        if self.entries is not None:
            fig1 = self.entries.vbt.signals.plot_as_entry_markers(self.open, fig=fig1)
            if osc_data is not None:  # Only plot if osc_data exists
                fig2 = self.entries.vbt.signals.plot_as_entry_markers(osc_data, fig=fig2)

        if self.exits is not None:
            fig1 = self.exits.vbt.signals.plot_as_exit_markers(self.open, fig=fig1)
            if osc_data is not None:  # Only plot if osc_data exists
                fig2 = self.exits.vbt.signals.plot_as_exit_markers(osc_data, fig=fig2)

        # Create a subplot figure with 2 rows, 1 column
        fig_combined = sp.make_subplots(rows=2, cols=1)

        # Add the traces from the first figure (fig1) to the first row of the subplot
        for trace in fig1['data']:
            fig_combined.add_trace(trace, row=1, col=1)

        # Add the traces from the second figure (fig2) to the second row of the subplot, if fig2 exists
        if fig2 is not None:
            for trace in fig2['data']:
                fig_combined.add_trace(trace, row=2, col=1)

        # Automatically add buy_threshold and sell_threshold to fig2 if they are not None
        if self.buy_threshold is not None:
            fig_combined.add_hline(y=self.buy_threshold, line_color='green', line_width=1.5, row=2, col=1)
        if self.sell_threshold is not None:
            fig_combined.add_hline(y=self.sell_threshold, line_color='red', line_width=1.5, row=2, col=1)

        # Optionally, update the layout of the combined figure
        fig_combined.update_layout(height=800, title_text="Combined Plot: Close Price and Oscillator Data", xaxis_rangeslider_visible=False)

        # Display the combined figure
        fig_combined.show()

    def generate_backtest(self):
        """Performs backtest and returns the stats"""
        init_cash = self.risk_object.balance
        size = None
        size_type = None
        accumulate = False

        if self.with_sizing:
            size = pd.Series(index=self.close.index, dtype='float')
            size[self.entries] = 10 #this sizing will be calculated through risk class
            size[self.exits] = np.inf

            size_type = 'value'
            accumulate = True

        self.portfolio = vbt.Portfolio.from_signals(
            close = self.open,
            entries = self.entries,
            exits = self.exits,
            size = size,
            size_type= size_type,
            accumulate= accumulate,
            init_cash= init_cash)

        return self.portfolio
    
    
    def set_granularity(self):
        # Retrieves multiple dates and compares then gets the most frequest
        time_differences = []
        for i in range(10):
            if i == 0:
                pass
            time_diff = self.df.index[i] - self.df.index[i-1]
            time_differences.append(time_diff)
        time_diff = max(time_differences, key=time_differences.count)


        time_map = {
            pd.Timedelta(minutes=1): 'ONE_MINUTE',
            pd.Timedelta(minutes=5): 'FIVE_MINUTE',
            pd.Timedelta(minutes=15): 'FIFTEEN_MINUTE',
            pd.Timedelta(minutes=30): 'THIRTY_MINUTE',
            pd.Timedelta(hours=1): 'ONE_HOUR',
            pd.Timedelta(hours=2): 'TWO_HOUR',
            pd.Timedelta(hours=6): 'SIX_HOUR',
            pd.Timedelta(days=1): 'ONE_DAY'
        }
        # Return the corresponding string or 'Unknown' if not found
        self.granularity = time_map.get(time_diff, 'Unknown')

    def add_adx(self, adx_buy_threshold, time_period):
        adx = ta.ADX(self.high, self.low, self.close, time_period)

        buy_signal = adx > adx_buy_threshold
        sell_signal = ~buy_signal

        adx_signals = self.generate_signals(buy_signal, sell_signal, with_formating=False)

        return adx_signals

