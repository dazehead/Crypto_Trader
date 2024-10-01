"""This needs to return signals"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import plotly.subplots as sp

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, df):
        self.df = df

        self.open = self.df['open']
        self.high = self.df['high']
        self.low = self.df['low']
        self.close = self.df['close']
        self.volume = self.df['volume']

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

        return signals

    def generate_signals(self, buy_signal, sell_signal, with_formating=True):
        """Common method to generate and format buy/sell signals"""
        signals = np.zeros_like(self.close, dtype=int)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        if with_formating:
            signals = self.format_signals(signals)

        # For graphing
        self.entries = np.zeros_like(signals, dtype=bool)
        self.exits = np.zeros_like(signals, dtype=bool)

        self.entries[signals == 1] = True
        self.exits[signals == -1] = True

        self.entries = pd.Series(self.entries, index=self.close.index)
        self.exits = pd.Series(self.exits, index=self.close.index)

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
                combined = 1  # Start with the most optimistic signal
                for signal in signals:
                    if signal[i] == -1:
                        combined = -1  # If any signal is -1, set combined to -1 and break
                        break
                    elif signal[i] == 0 and combined != -1:
                        combined = 0  # If any signal is 0 and no -1 encountered, set combined to 0
                combined_signals.append(combined)
        except Exception as e:
            print(f"Invalid signals: {e}")
        
        combined_signals = self.format_signals(combined_signals)

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
        fig1 = self.close.vbt.plot(trace_kwargs=dict(name='Close'))
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
            fig1 = self.entries.vbt.signals.plot_as_entry_markers(self.close, fig=fig1)
            if osc_data is not None:  # Only plot if osc_data exists
                fig2 = self.entries.vbt.signals.plot_as_entry_markers(osc_data, fig=fig2)

        if self.exits is not None:
            fig1 = self.exits.vbt.signals.plot_as_exit_markers(self.close, fig=fig1)
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
        fig_combined.update_layout(height=800, title_text="Combined Plot: Close Price and Oscillator Data")

        # Display the combined figure
        fig_combined.show()

    def generate_backtest(self):
        """Performs backtest and returns the stats"""
        self.portfolio = vbt.Portfolio.from_signals(self.close, self.entries, self.exits)

        return self.portfolio