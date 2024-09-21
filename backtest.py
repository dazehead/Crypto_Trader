import vectorbt as vbt
import pandas as pd

class Backtest:
    def __init__(self, strategy_object):
        self.strategy = strategy_object

        self.close = self.strategy.close
        self.open = self.strategy.open
        self.high = self.strategy.high
        self.low = self.strategy.low
        self.volume = self.strategy.volume
        
        self.entries = self.strategy.entries
        self.exits = self.strategy.exits


    def graph_strat(self, **kwargs):
        """Graphs the strategy with entry and exit markers"""
        param_number = 0
        for key, value in kwargs.items():
            param_number += 1
            setattr(self, key, value)

        fig = self.strategy.df['close'].vbt.plot(trace_kwargs=dict(name='Close'))
        fig = self.strategy.ti_data.vbt.plot(trace_kwargs=dict(name=self.ti_data_name), fig=fig)
        if param_number > 1:
            fig = self.strategy.ti2_data.vbt.plot(trace_kwargs=dict(name=self.ti2_data_name), fig=fig)
            if param_number > 2:
                fig = self.strategy.ti3_data.vbt.plot(trace_kwargs=dict(name=self.ti3_data_name), fig=fig)
        fig = self.entries.vbt.signals.plot_as_entry_markers(self.close, fig=fig)
        fig = self.exits.vbt.signals.plot_as_exit_markers(self.close, fig=fig)
        fig.show()
    
    def generate_backtest(self):
        """Performs backtest and returns the stats"""
        portfolio_trade = vbt.Portfolio.from_signals(self.close, self.entries, self.exits)
        stats = portfolio_trade.stats()

        return stats
