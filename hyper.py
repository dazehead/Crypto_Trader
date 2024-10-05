import vectorbt as vbt
import numpy as np
from strategies.strategy import Strategy
import talib

class Hyper(Strategy):
    """A class to handle Hyper Optimization backtests"""
    def __init__(self, strategy_object, **kwargs):
        """Initiates strategy resources"""
        super().__init__(df=strategy_object.df)  # Provide df here
        self.strategy_object = strategy_object  # Save the strategy object

        possible_inputs = ['open', 'high', 'low', 'close', 'volume']
        self.input_names = []
        self.inputs = []
        self.params = {}
        for key, value in kwargs.items():
            if key in possible_inputs:
                self.input_names.append(key)
                self.inputs.append(value)
                setattr(self, key, value)
            else:
                self.params[key] = value

        self.ind = self.build_indicator_factory()
        self.res = self.generate_signals()
        self.entries, self.exits = self.convert_signals()
        self.pf = self.run_portfolio()
        self.returns = self.pf.total_return()
        self.max = self.returns.max()

    def build_indicator_factory(self):
        """Builds the Indicator Factory"""
        param_names = list(self.params.keys())

        ind = vbt.IndicatorFactory(
            class_name="Custom",
            short_name="cust",
            input_names=self.input_names,
            param_names=param_names,
            output_names=['value']
        ).from_apply_func(
            self.strategy_object.custom_indicator,
            to_2d=False
        )
        return ind

    
    def generate_signals(self):
        """Generates the entries/exits signals"""
        try:
            res = self.ind.run(
                *self.inputs,
                **self.params,
                param_product=True
            )
        except Exception as e:
            print(f"Error during signal generation: {e}")
            res = None  # Handle as needed
        return res
    
    def convert_signals(self):
        """Converts signals to entries and exits"""
        entries = self.res.value == 1.0
        exits = self.res.value == -1.0
        return entries, exits
    

    def run_portfolio(self):
        """performing backtest"""
        close_data = getattr(self, 'close', self.close)
        pf = vbt.Portfolio.from_signals(
            close_data, 
            self.entries,
            self.exits
        )
        return pf