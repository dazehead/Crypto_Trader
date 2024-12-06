import vectorbt as vbt
import numpy as np
import pandas as pd
from core.strategies.strategy import Strategy
import talib

class Hyper(Strategy):
    """A class to handle Hyper Optimization backtests"""
    def __init__(self, strategy_object, **kwargs):
        """Initiates strategy resources"""
        dict_df = {strategy_object.symbol: strategy_object.df}
        super().__init__(dict_df=dict_df)
        self.strategy = strategy_object
        if self.strategy.risk_object is not None:
            self.risk_object = self.strategy.risk_object
        self.with_sizing = self.strategy.with_sizing

        
        possible_inputs = ['open', 'high', 'low', 'close', 'volume']
        self.input_names = []
        self.inputs = []
        self.params = {}
        for key, value in kwargs.items():
            if key in possible_inputs:
                self.input_names.append(key)
                self.inputs.append(value)
                setattr(self, key, value) # dont think we need this it sets self.close = object
            else:
                self.params[key] = value

        self.ind = self.build_indicator_factory()
        self.res = self.generate_signals()
        self.entries, self.exits = self.convert_signals()
        self.pf = self.run_portfolio()
        self.returns = self.pf.total_return() #to view print(self.returns.to_string())
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
            self.strategy.custom_indicator,
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
    

    # def run_portfolio(self):
    #     """performing backtest"""
    #     close_data = getattr(self, 'close', self.close)
    #     open_data = getattr(self, 'open', self.open )
    #     pf = vbt.Portfolio.from_signals(
    #         close_data, 
    #         self.entries,
    #         self.exits
    #     )
    #     return pf
    

    def run_portfolio(self):
        """Performs backtest and returns the stats"""
        if self.risk_object is not None:
            init_cash = self.risk_object.total_balance
        size = None
        size_type = None
        accumulate = False

        if self.with_sizing:
            # size = np.full(self.entries.shape, np.nan)
            # size[self.entries.to_numpy()] = self.risk_object.percent_to_size
            # size[self.exits.to_numpy()] = np.inf

            size = pd.DataFrame(np.nan, index=self.entries.index, columns=self.entries.columns)
            size[self.entries] = self.risk_object.percent_to_size #this sizing will be calculated through risk class
            size[self.exits] = np.inf


            size_type = 'value'
            accumulate = True


        granularity_to_freq = {
            'ONE_MINUTE': '1min',
            'FIVE_MINUTE': '5min',
            'FIFTEEN_MINUTE': '15min',
            'THIRTY_MINUTE': '30min',
            'ONE_HOUR': '1h',
            'TWO_HOUR': '2h',
            'SIX_HOUR': '6h',
            'ONE_DAY': '1D'
        }

        # Convert granularity to frequency
        freq = granularity_to_freq.get(self.granularity, None)
        if freq is None:
            raise ValueError(f"Unsupported granularity: {self.granularity}")

        # Run the backtest
        pf = vbt.Portfolio.from_signals(
            close=self.close,
            entries=self.entries,
            exits=self.exits,
            size=size,
            freq=freq,
            size_type=size_type,
            accumulate=accumulate,
            init_cash=init_cash
        )
       

        return pf