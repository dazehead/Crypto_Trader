import vectorbt as vbt
import numpy as np
from backtest import Backtest

class Hyper(Backtest):
    """A class to handle Hyper Optimization backtests"""
    def __init__(self, strategy_object):
        """Initiates strategy resources"""
        super().__init__(strategy_object=strategy_object)

        self.ind = self.build_indicator_factory()
        self.res = self.generate_signals()
        self.entries, self.exits = self.convert_signals()
        self.pf = self.run_portfolio()
        self.returns = self.pf.total_return() #to view print(self.returns.to_string())
        self.max = self.returns.max()


    def build_indicator_factory(self):
        """Builds the Indicator Factory"""
        ind = vbt.IndicatorFactory(
            class_name="Custom",
            short_name="cust",
            input_names=['close'],
            param_names=['fast_window', 'slow_window'],
            output_names=['value']
        ).from_apply_func(
            self.strategy.custom_indicator,
            to_2d=False
        )
        return ind
    
    def generate_signals(self):
        """Generates the entries/exits signals"""

        res = self.ind.run(
            self.close,
            fast_window=np.arange(10,40, step=5, dtype=int),
            slow_window=np.arange(70, 80, step=2, dtype=int),
            param_product=True
        )
        return res
    
    def convert_signals(self):
        """Converts signals to entries and exits"""
        entries = self.res.value == 1.0
        exits = self.res.value == -1.0
        return entries, exits
    

    def run_portfolio(self):
        """performing backtest"""
        pf = vbt.Portfolio.from_signals(
            self.close,
            self.entries,
            self.exits
        )
        return pf