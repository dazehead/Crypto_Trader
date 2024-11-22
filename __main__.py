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
from strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
import datetime as dt
import pandas as pd

granularity = 'ONE_MINUTE'
symbol = 'XBTUSD'
counter = 0


def on_message():
    print('--------------------------------------------------------------------------------------\n')
    global counter
    global kraken
    global risk
    global scanner
    global df_manager
    print(f'counter: {counter}')
    
    for k, v in df_manager.dict_df.items():

        if dt.datetime.now() <= df_manager.next_update_time[k]:
            continue
        print(k)
        df_manager.data_for_live_trade(symbol=k, update=True)
        current_dict = {k:v}

        strat = RSI_ADX_GPU(current_dict, risk, with_sizing=True)

        strat.custom_indicator(strat.close_gpu, *risk.symbol_params[k])

        trade = Trade(risk = risk,
                    strat_object=strat,
                    logbook=logbook)
        
        df_manager.set_next_update(k)
        print('\n-------------------------------------------------------------------------------------\n')

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
risk = Risk_Handler(kraken)
scanner = Scanner(client=kraken)
df_manager = DF_Manager(scanner)
scanner.assign_attribute(df_manager=df_manager)

scanner.coinbase.get_candles_for_db(scanner.coinbase_crypto, kraken.granularity, days=30)


for symbol in scanner.kraken_crypto:
    strat = RSI_ADX_GPU(dict_df= None, risk_object=risk)
    strat.symbol = symbol
    params = database_interaction.get_best_params(strat, df_manager,live_trading=True, best_of_all_granularities=True, minimum_trades=3)
    risk.symbol_params[symbol] = params
    df_manager.set_next_update(symbol, initial=True)
logbook = LinkedList()


async def main():
    await fetch_data_periodically()

if __name__ == "__main__":
    asyncio.run(main())
