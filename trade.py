import pickling

class Trade():
    """This class will have all logic for executing trades"""

    def __init__(self,risk,strat_object, logbook, signals = None):
        self.risk = risk
        self.strat = strat_object
        self.logbook = logbook
        self.client = self.risk.client
        self.symbol = self.strat.symbol

        self.signals = self.strat.signals     
        if signals:
            self.signals = signals



        if self.signals[-1] == 1:
            self.buy()

        elif self.signals[-1] == -1:
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):

        print(f'BUY: {self.risk.amount_to_purchase}')

    def sell(self):
        print(f'SELL: all open positions from client.get_open_positions(self.symbol)')

    def monitor_trade(self):
        """
        perform some sort of risk analysis to ensure the trade is still profitable
        and possibly re-buy if it is going well or sell if it is going bad
        
        """
        print('monitoring trades')
