import pickling

class Trade():
    """This class will have all logic for executing trades"""

    def __init__(self,risk,strat_object, logbook, rest_client, signals: list=None):
        self.risk = risk
        self.strat = strat_object
        self.logbook = logbook
        self.client = rest_client
        self.symbol = self.strat.symbol
        self.quote_size = self.risk.quote_size

        if signals:
            self.signals = signals
        else:
            self.signals = self.strat.signals


        if self.signals[-1] == 1:
            self.buy()

        elif self.signals[-1] == -1:
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):
        """we might need to use list fills to see what the status of the fills are
        just in case they dont fill we need to make a loop to update the orders and refill"""
        
        pickling.to_pickle('balance_before_buy', self.risk.total_balance)

        buy_order = self.client.market_order_buy(client_order_id = '1',
                                     product_id = self.symbol,
                                     quote_size = self.quote_size)
        pickling.to_pickle('buy_order', buy_order)

        self.risk.get_portfolio_info()
        pickling.to_pickle('balance_after_buy', self.risk.total_balance)
        print('should buy at this point')



    def sell(self):
        """we might need to use list fills to see what the status of the fills are
        just in case they dont fill we need to make a loop to update the orders and refill"""

        self.risk.get_portfolio_info()
        pickling.to_pickle('balance_before_sell', self.risk.total_balance)
        sell_order = self.client.market_order_sell(clinet_order_id = '2',
                                                   product_id = self.symbol,
                                                   quote_size = self.quote_size)
        pickling.to_pickle('sell_order', sell_order)
        self.risk.get_portfolio_info()
        pickling.to_pickel('balance_after_sell', self.risk.total_balance)
        print('should sell at this point')
        pass

    def monitor_trade(self):
        """
        perform some sort of risk analysis to ensure the trade is still profitable
        and possibly re-buy if it is going well or sell if it is going bad
        
        """
        print('monitoring trades')
        pass
