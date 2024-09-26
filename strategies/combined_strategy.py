from strategies.strategy import Strategy

class Combined_Strategy(Strategy):
    def __init__(self, df, *strategies):
        Strategy.__init__(self, df)
        self.strategies = strategies
        
        for strategy in self.strategies:
            strategy.__init__(self, df) 
            # we are initializing the strategies saved in self.strategies
            # even though we having manually done it the strategies saved in self.strategies are now initialized and available for use

    def generate_combined_signals(self):
        signals = [strategy.custom_indicator(self) for strategy in self.strategies] # have we seen list comprehension before???
        combined_signals = self.combine_signals(*signals)
        return combined_signals

    def graph(self):
        """
        before we make this we will need to fix the lines that we have to manually type in the strategy.graph() function
        also i THINK i need to make extract ti1_data and osc1_data for each strategy and assign them new values after we run __init__ and rename them
        like strat_1_ti1_data or better idea strategy.__class__.__name__ so it saves as RSI.ti1_data so that theres not duplicate ti1_data 
        and then dynamically graph all ti_data to the first graph and then all
        osc_data to the second graph--this might take a little bit
        """
        pass