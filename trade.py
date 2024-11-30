import pickling
import math
import time
import database_interaction

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
        self.total_volume_owned = self.client.get_extended_balance(self.symbol)

        self.signals = self.strat.signals     
        if signals:
            self.signals = signals



        if self.signals[-1] == 1:
            if self.client.get_account_balance() <= self.volume_to_risk:
                print('*****NO MORE MULA*********')
            else:
                self.buy()

        elif self.signals[-1] == -1:
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):
        print('BUY')
        buy_order = self.client.add_order(
            type_of_order= 'buy',
            symbol = self.symbol,
            volume= self.risk.volume_to_risk,
            price = self.current_asset_price,
            pickle=True)
        time.sleep(.25)

        # if True it will keep looping until there are no open orders
        while self.client.any_open_orders():
            order_id =buy_order['result']['txid'][0]
            buy_order = self.client.edit_order(
                order_id = order_id,
                symbol = self.symbol,
                volume = self.risk.volume_to_risk,
                price = self.client.get_recent_spreads(
                    symbol=self.symbol,
                    type_of_order= 'buy'
                    )          
            )
            time.sleep(.25)
            database_interaction.trade_export(buy_order, self.get_balance_to_risk())

            """edit the open order until it fills"""
        #print(buy_order)

    def sell(self):
        print('SELL')
        sell_order = self.client.add_order(
            type_of_order= 'sell',
            symbol = self.symbol,
            volume = self.total_volume_owned,
            price = self.current_asset_price,
            pickle=True)
        #print(sell_order)
        time.sleep(1)

        while self.client.any_open_orders():
            print(sell_order)
            order_id =sell_order['result']['txid'][0]
            sell_order = self.client.edit_order(
                order_id = order_id,
                symbol = self.symbol,
                volume = self.risk.volume_to_risk,
                price = self.client.get_recent_spreads(
                    symbol=self.symbol,
                    type_of_order= 'sell'
                    )          
            )
            time.sleep(.25)
        database_interaction.trade_export(sell_order, self.get_balance_to_risk())
        

    def monitor_trade(self):
        print('monitoring')
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
        self.risk.volume_to_risk = minimum
        return minimum
        # minimum_price = (math.ceil((self.current_asset_price* minimum)*10) /10) + .05
        # desired = self.risk.total_balance *.005

        # """here is where we need to calculate our volume to send to add_order using self.current_asset_price calculated with the minium volume"""
        # if minimum_price > desired:
        #     self.risk.volume_to_risk = minimum_price
        #     return minimum_price
        # self.risk.volume_to_risk = desired
        # return desired
