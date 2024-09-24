import vectorbt as vbt
import pandas as pd
import plotly.subplots as sp

class Backtest:
    def __init__(self, strategy_object):
        self.strategy = strategy_object

        self.close = self.strategy.close
        self.open = self.strategy.open
        self.high = self.strategy.high
        self.low = self.strategy.low
        #self.volume = self.strategy.volume
        
        self.entries = self.strategy.entries
        self.exits = self.strategy.exits



    def graph_strat(self):
        """----NOTE: ALL DATA MUST BE PD.SERIES----"""

        # Start by plotting the first figure (Close price)
        param_number = 0
        fig = self.strategy.df['close'].vbt.plot(trace_kwargs=dict(name='Close'))
        fig2 = None

        # Loop over param_numbers to dynamically access ti_data and osc_data
        while True:
            param_number += 1

            # Dynamically access ti{i}_data and check if it's not None
            ti_data_attr = getattr(self.strategy, f"ti{param_number}_data", None)
            
            if ti_data_attr is not None:
                ti_data_name, ti_data = ti_data_attr  # Unpack the tuple (name, data)
                if ti_data is not None:
                    ti_data = pd.Series(ti_data, index=self.close.index)
                    fig = ti_data.vbt.plot(trace_kwargs=dict(name=ti_data_name), fig=fig)

            # Dynamically access osc{i}_data and check if it's not None
            osc_data_attr = getattr(self.strategy, f"osc{param_number}_data", None)
            
            if osc_data_attr is not None:
                osc_data_name, osc_data = osc_data_attr  # Unpack the tuple (name, data)
                if osc_data is not None:
                    osc_data = pd.Series(osc_data, index=self.close.index)
                    if fig2 is None:
                        fig2 = osc_data.vbt.plot(trace_kwargs=dict(name=osc_data_name))
                    else:
                        fig2 = osc_data.vbt.plot(trace_kwargs=dict(name=osc_data_name), fig=fig2)

            # Break the loop if both ti_data and osc_data for the current param_number are None
            if ti_data_attr is None and osc_data_attr is None:
                break

        # Plot entry and exit markers on the first figure
        fig = self.entries.vbt.signals.plot_as_entry_markers(self.close, fig=fig)
        fig = self.exits.vbt.signals.plot_as_exit_markers(self.close, fig=fig)

        # Create a subplot figure with 2 rows, 1 column
        fig_combined = sp.make_subplots(rows=2, cols=1)

        # Add the traces from the first figure (fig) to the first row of the subplot
        for trace in fig['data']:
            fig_combined.add_trace(trace, row=1, col=1)

        # Add the traces from the second figure (fig2) to the second row of the subplot
        if 'fig2' in locals():  # Only add fig2 if osc data was found and plotted
            for trace in fig2['data']:
                fig_combined.add_trace(trace, row=2, col=1)

        # Optionally, update the layout of the combined figure
        fig_combined.update_layout(height=800, title_text="Combined Plot: Close Price and Oscillator Data")

        # Display the combined figure
        fig_combined.show()

    
    def generate_backtest(self):
        """Performs backtest and returns the stats"""
        portfolio_trade = vbt.Portfolio.from_signals(self.close, self.entries, self.exits)
        stats = portfolio_trade.stats()

        return stats
