"""This class will have all logic for executing trades"""
class Trade():

    def __init__(self, strat_object, logbook, rest_client):
        self.logbook = logbook
        self.client = rest_client
        self.strat = strat_object
        self.signals = self.strat.signals
        self.symbol = self.strat.symbol
        # 

        if self.signals[-1] == 1:
            self.buy()

        elif self.signals[-1] == -1:
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):
        # self.client.market_order_buy(client_order_id = '1',
        #                              product_id = self.symbol,
        #                              quote_size = '.50')
        print('should buy at this point')



    def sell(self):
        """
        trade_execution = rest_client.execute the trade
        logbook.log_trade(trade_execution)
        """
        print('should sell at this point')
        pass

    def monitor_trade(self):
        """
        perform some sort of risk analysis to ensure the trade is still profitable
        and possibly re-buy if it is going well or sell if it is going bad
        
        """
        print('monitoring trades')
        pass
