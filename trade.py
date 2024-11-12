import pickling
import math

class Trade():
    """This class will have all logic for executing trades"""

    def __init__(self,risk,strat_object, logbook, signals = None):
        self.risk = risk
        self.strat = strat_object
        self.logbook = logbook
        self.client = self.risk.client
        self.symbol = self.strat.symbol
        self.current_asset_price = float(self.strat.close.iloc[-1])
        self.volume_to_risk = self.get_balance_to_risk()
        print(f"calculated volume to risk: {self.volume_to_risk}")
        #print(f'volume_to_buy: {self.volume_to_risk}')

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
        print(self.risk.balance_to_risk)
        buy_order = self.client.add_order(
            type_of_order= 'buy',
            symbol = self.symbol,
            volume= self.risk.balance_to_risk,
            pickle=True)
        print(buy_order)

    def sell(self):
        sell_order = self.client.add_order(
            type_of_order= 'buy',
            symbol = self.symbol,
            pickle=True)
        print(sell_order)
        

    def monitor_trade(self):
        pass
        #print(f'...monitoring trade for {self.symbol}')
        """
        perform some sort of risk analysis to ensure the trade is still profitable
        and possibly re-buy if it is going well or sell if it is going bad
        
        """

    def get_balance_to_risk(self):
        """Calculates balance to risk based off of backtests"""
        minimum_volume = {
            'XXBTZUSD': 0.00005,
            'XETHZUSD': 0.002,
            'XDGUSD': 30,
            'SHIBUSD': 200000,
            'AVAXUSD': .1,
            'BCHUSD': .01,
            'LINKUSD': .2,
            'UNIUSD': .5,
            'XLTCZUSD': .05,
            'XXLMZUSD': 40,
            'XETCZUSD': .3,
            'AAVEUSD': .03,
            'XTZUSD': 4,
            'COMPUSD': .1
        }
        minimum = minimum_volume[self.symbol]
        minimum_price = math.ceil((self.current_asset_price* minimum)*100) /100
        desired = self.risk.total_balance *.005

        """here is where we need to calculate our volume to send to add_order using self.current_asset_price calculated with the minium volume"""
        if minimum_price > desired:
            return minimum_price
        return desired
