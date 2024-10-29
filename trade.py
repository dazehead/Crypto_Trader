import pickling

class Trade():
    """This class will have all logic for executing trades"""

    def __init__(self,risk,strat_object, logbook):
        self.risk = risk
        self.strat = strat_object
        self.logbook = logbook
        self.client = self.risk.client
        self.symbol = self.strat.symbol
        self.quote_size = self.risk.quote_size

        self.signals = self.strat.symbols


        if self.signals[-1] == 1:
            self.buy()

        elif self.signals[-1] == -1:
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):
        print('BUY')
        



    def sell(self):
        print('SELL')

    def monitor_trade(self):
        """
        perform some sort of risk analysis to ensure the trade is still profitable
        and possibly re-buy if it is going well or sell if it is going bad
        
        """
        print('monitoring trades')
