"""This class will have all logic for executing trades"""
class Trade():

    def __init__(self, signals, logbook, rest_client):
        self.signals = signals
        self.logbook = logbook
        self.rest_client = rest_client

        if self.signals[-1] == 1:
            self.buy()

        elif self.signals[-1] == -1:
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):
        """
        trade_execution = rest_client.execute the trade
        logbook.log_trade(trade_execution)
        """
        pass

    def sell(self):
        """
        trade_execution = rest_client.execute the trade
        logbook.log_trade(trade_execution)
        """
        pass

    def monitor_trade(self):
        """
        perform some sort of risk analysis to ensure the trade is still profitable
        and possibly re-buy if it is going well or sell if it is going bad
        
        """
        pass
