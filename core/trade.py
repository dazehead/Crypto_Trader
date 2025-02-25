import core.pickling
import math
import time
import core.database_interaction as database_interaction

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
            account_balance = self.client.get_account_balance()
            at_risk = self.volume_to_risk
            if account_balance <= at_risk:
                print('*****NO MORE MULA*********')
                print(f"Cash Balance: {account_balance}\nAt Risk: {at_risk}")
            else:
                self.buy()

        elif self.signals[-1] == -1:
            pass
            self.sell()

        else:
            self.monitor_trade()


    def buy(self):
        print('BUY')
        try:
            # Create buy order
            buy_order = self.client.add_order(
                type_of_order='buy',
                symbol=self.symbol,
                volume=self.risk.volume_to_risk * 2,
                price=self.current_asset_price
                )
            time.sleep(1)

            # Edit open orders until filled
            while self.client.any_open_orders():
                try:
                    if buy_order and 'result' in buy_order and 'txid' in buy_order['result']:
                        order_id = buy_order['result']['txid'][0]
                        buy_order = self.client.edit_order(
                            order_id=order_id,
                            symbol=self.symbol,
                            volume=self.risk.volume_to_risk,
                            price=self.client.get_recent_spreads(
                                symbol=self.symbol,
                                type_of_order='buy'
                            )
                        )
                    else:
                        print("Invalid buy_order structure or no txid:", buy_order)
                        break
                except Exception as e:
                    print(f"Error while editing order: {e}")
                    break
                time.sleep(0.25)

            # Export trade details to the database
            if buy_order:
                try:
                    database_interaction.trade_export(
                        buy_order,
                        balance=self.client.get_account_balance()
                    )
                except Exception as e:
                    print(f"Error while exporting trade: {e}")
            else:
                print("Buy order is None, skipping export.")
        except Exception as e:
            print(f"Error in buy method: {e}")


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
        database_interaction.trade_export(sell_order, balance=self.client.get_account_balance())
        
    def futures_trade(self):
        # Define variables for the futures order
        process_before = "2024-12-31 23:59:59.000000+00:00"  # Example timestamp
        order_type = "lmt"  # Order type: 'lmt', 'post', 'ioc', 'mkt', etc.
        type_of_order = "buy"  # 'buy' or 'sell'
        limit_price = 40000  # Example limit price
        stop_price = 39000  # Example stop price
        try:
            future_order = self.add_order_futures(
                process_before=process_before,
                order_type=order_type,
                symbol=self.symbol,
                type_of_order=type_of_order,
                limit_price=limit_price,
                stop_price=stop_price
            )

            if future_order:
                try:
                    database_interaction.trade_export(
                        future_order,
                        balance=self.client.get_account_balance()
                    )
                except Exception as e:
                    print(f"Error while exporting trade: {e}")
            else:
                print("Buy order is None, skipping export.")

    # Handle and return the response
        except Exception as e:
            print(f"Error in futures_trade method: {e}")

 
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
