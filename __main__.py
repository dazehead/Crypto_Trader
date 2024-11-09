import time
import os
import coinbase_wrapper
import asyncio
import database_interaction
from coinbase.websocket import WSClient, WSClientConnectionClosedException
from coinbase.rest import RESTClient
from dataframe_manager import DF_Manager
from strategies.strategy import Strategy
from strategies.single.rsi import RSI
from trade import Trade
from log import LinkedList
from scanner import Scanner
from risk import Risk_Handler
from kraken_wrapper import Kraken
from strategies.double.rsi_adx import RSI_ADX

interval = 'FIVE_MINUTE'
symbol = 'XBTUSD'
counter = 0


def on_message():
    global counter
    global kraken
    global risk
    print(f'counter: {counter}')
    df_manager.data_for_live_trade(update=True)

    for k, v in df_manager.dict_df.items():
        current_dict = {k:v}
        
        """grab best parameters for symbols and run the strategy with those parametrs"""
        strat = RSI_ADX(current_dict, risk)
        params = database_interaction.get_best_params(strat)
        strat.custom_indicator(strat.close, *params)
        print(strat.rsi_window,strat.buy_threshold,strat.sell_threshold,strat.adx_buy_threshold,strat.adx_time_period)
        print(params)
        signals = [0,1,-1,0]
        
        trade = Trade(risk = risk,
                    strat_object=strat,
                    logbook=logbook,
                    signals=[signals[counter]])
    
    counter += 1


async def fetch_data_periodically():
    while True:
        start_time = time.time()

        on_message()

        execution_time = time.time() - start_time
        sleep_time = max(0, kraken.time_to_wait - execution_time)

        print(f"Execution time: {execution_time:.2f} seconds. Sleeping for {sleep_time:.2f} seconds.\n")

        await asyncio.sleep(sleep_time)


"""---------------start of program-----------------"""
kraken = Kraken(interval=interval)
scanner = Scanner(client=kraken)
df_manager = DF_Manager(scanner)

scanner.assign_attribute(df_manager=df_manager)
scanner.populate_manager(days_ago=2)

"""Loops through the scanner until a product gets returned from our defined filter parameters"""
while not scanner.products_to_trade:
    scanner.filter_products()


logbook = LinkedList()
risk = Risk_Handler(kraken)



async def main():
    await fetch_data_periodically()

if __name__ == "__main__":
    asyncio.run(main())
