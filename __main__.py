import time
import os
import wrapper
from coinbase.websocket import WSClient, WSClientConnectionClosedException
from coinbase.rest import RESTClient
from dataframe_manager import DF_Manager
from strategies.strategy import Strategy
from trade import Trade
from log import LinkedList
from scanner import Scanner

granularity = 'ONE_MINUTE'

def on_message(msg):
    """
    function that gets called everytime a new message appears
    we will need only send msg to a our Trade function so it can montior the trade
    for any issues during execution
    
    """
    
    df_manager.process_message(msg)

    ma_strat = Strategy(df_manager.df) # slow ma data

    signals = ma_strat.custom_indicator(ma_strat.close,
                                        fast_window=2,
                                        slow_window=66)
    
    trade = Trade(signals=signals,
                  logbook=logbook,
                  rest_client=rest_client)



"""---------------start of program-----------------"""
global df_manager
global rest_client
api_key = os.getenv('API_ENV_KEY')
api_secret = os.getenv('API_SECRET_ENV_KEY')

granularity = 'ONE_MINUTE'


ws_client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, retry=False)
rest_client = RESTClient(api_key=api_key, api_secret=api_secret)

scanner = Scanner(rest_client=rest_client,
                  granularity=granularity)

"""Loops through the scanner until a product gets returned from our defined filter parameters"""
while not scanner.products_to_trade:
    scanner.filter_products()
df_manager = DF_Manager(scanner)

logbook = LinkedList()



def connect_and_subscribe():
    "function to connect subscribe and then reconnect after 20 seconds"
    try:
        ws_client.open()
        ws_client.subscribe(product_ids=[scanner.products_to_trade], channels=['candles', 'heartbeats', 'user'])
        ws_client.run_forever_with_exception_check()

    except WSClientConnectionClosedException as e:
        print("Connection closed! Sleeping for 20 seconds before reconnecting...")
        time.sleep(20)
        connect_and_subscribe()

    except Exception as e:
        """suppose to catch any error and stop the program but it still runs"""
        print(f"An error occured:\n{e}")
        print("Stopping the program.")
        raise
connect_and_subscribe()

