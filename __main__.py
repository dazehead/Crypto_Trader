import time
import os
import wrapper
import asyncio
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

interval = 'ONE_MINUTE'
symbol = 'XBTUSD'
counter = 0


def on_message():
    global counter
    global kraken
    global risk
    kraken.get_trade_volume()

    print(f'counter: {counter}')
    df_manager.data_for_live_trade(update=True)


    strat = RSI(df_manager.dict_df)
    strat.custom_indicator(strat.close)
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
kraken = Kraken()
scanner = Scanner(client=kraken)

"""Loops through the scanner until a product gets returned from our defined filter parameters"""
while not scanner.products_to_trade:
    scanner.filter_products()

df_manager = DF_Manager(scanner)

logbook = LinkedList()
risk = Risk_Handler(kraken)



async def main():
    await fetch_data_periodically()

if __name__ == "__main__":
    asyncio.run(main())
