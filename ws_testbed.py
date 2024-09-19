"""dont need to use async because ws client has built in"""
import time
import os
from coinbase.websocket import WSClient, WSClientConnectionClosedException
from dataframe_manager import DF_Manager

api_key = os.getenv('API_ENV_KEY')
api_secret = os.getenv('API_SECRET_ENV_KEY')

product_id = 'BTC-USD'

#####################################################
"continious market data for given time"
def market_data_subscription():
    global df_manager
    def on_message(msg):
        print("------------------------------------")
        df_manager.process_message(msg)
        print('\n')

    def on_open():
        print("connection opened!")

    client = WSClient(api_key=api_key,
                    api_secret=api_secret,
                    on_message=on_message,
                    on_open=on_open)
    df_manager = DF_Manager()

    client.open()
    client.subscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])

    time.sleep(10)

    client.unsubscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])
    client.close()
#market_data_subscription()


#################################
"""aysnc functionality running forever  ctl+C to exit"""
def run_forever_market_data():
    global df_manager

    def on_message(msg):
        "function that gets called when new data comes in"
        print('----------------------------------------------')
        #print(msg)
        df_manager.process_message(msg)

    """---------------start of program-----------------"""
    client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, retry=False)
    df_manager = DF_Manager()

    def connect_and_subscribe():
        "function to connect subscribe and then reconnect after 20 seconds"
        try:
            client.open()
            client.subscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])
            client.run_forever_with_exception_check()
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

run_forever_market_data()