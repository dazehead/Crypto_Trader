import time
import os
import wrapper
import asyncio
from coinbase.websocket import WSClient, WSClientConnectionClosedException
from coinbase.rest import RESTClient
from dataframe_manager import DF_Manager
from strategies.strategy import Strategy
from strategies.rsi import RSI
from trade import Trade
from log import LinkedList
from scanner import Scanner
from risk import Risk_Handler

granularity = 'ONE_MINUTE'
symbol = 'BTC-USD'
counter = 0
granularity_mapping = {
    'ONE_MINUTE': 60,
    'FIVE_MINUTES': 300,
    'FIFTEEN_MINUTES': 900,
    'ONE_HOUR': 3600,
    'ONE_DAY': 86400
}

def on_message():
    global counter
    global df_manager
    global rest_client
    global risk
    print(counter)
    
    df_manager.data_for_live_trade(update=True)

    strat = RSI(df_manager.dict_df) # slow ma data
    strat.custom_indicator(strat.close)
    signals = [0,1,-1,0]
    
    trade = Trade(risk = risk,
                  strat_object=strat,
                  logbook=logbook,
                  rest_client=rest_client,
                  signals=[signals[counter]])
    
    counter += 1


async def fetch_data_periodically():
    while True:
        start_time = time.time()

        on_message()

        execution_time = time.time() - start_time
        sleep_time = max(0, granularity_mapping[granularity] - execution_time)

        print(f"Execution time: {execution_time:.2f} seconds. Sleeping for {sleep_time:.2f} seconds.")

        await asyncio.sleep(sleep_time)


"""---------------start of program-----------------"""
api_key = os.getenv('API_ENV_KEY')
api_secret = os.getenv('API_SECRET_ENV_KEY')

granularity = 'ONE_MINUTE'


ws_client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, retry=False)
rest_client = RESTClient(api_key=api_key, api_secret=api_secret)

scanner = Scanner(rest_client=rest_client,
                  granularity=granularity)

"""Loops through the scanner until a product gets returned from our defined filter parameters"""
while not scanner.products_to_trade:
    scanner.filter_products('SPOT')

df_manager = DF_Manager(scanner)

logbook = LinkedList()
risk = Risk_Handler(rest_client)



async def main():
    await fetch_data_periodically()

if __name__ == "__main__":
    asyncio.run(main())
