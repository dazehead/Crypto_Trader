import vectorbt as vbt
import pandas as pd

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


    def graph_strat(self, **kwargs):
        """----NOTE: ALL DATA MUST BE PD.SERIES----"""

        """Graphs the strategy with entry and exit markers"""
        # Create a figure with the 'close' prices
        param_number = 0
        fig = self.strategy.df['close'].vbt.plot(trace_kwargs=dict(name='Close'))

        # Loop over kwargs, set attributes dynamically, and plot ti_data if it's not None
        for key, value in kwargs.items():
            param_number += 1
            setattr(self, key, value)
            
            # Dynamically access the ti{i}_data attribute and check if it's not None
            ti_data_attr = getattr(self.strategy, f"ti{param_number}_data", None)
            
            if ti_data_attr is not None:  # Ensure it's not None before plotting
                ti_data_name_attr = getattr(self, f"ti{param_number}_data_name", None)
                
                if ti_data_name_attr:  # Ensure the name attribute exists
                    fig = ti_data_attr.vbt.plot(trace_kwargs=dict(name=ti_data_name_attr), fig=fig)

        # Plot entry and exit markers
        fig = self.entries.vbt.signals.plot_as_entry_markers(self.close, fig=fig)
        fig = self.exits.vbt.signals.plot_as_exit_markers(self.close, fig=fig)

        fig2 = self.strategy.osc1_data.vbt.plot(trace_kwargs=dict(name='20-day Volume'))

        # Display the figure
        fig.show()
    
    def generate_backtest(self):
        """Performs backtest and returns the stats"""
        portfolio_trade = vbt.Portfolio.from_signals(self.close, self.entries, self.exits)
        stats = portfolio_trade.stats()

        return stats
