"""dont need to use async because ws client has built in"""
import time
import os
from coinbase.websocket import WSClient, WSClientConnectionClosedException
from utils import to_df

api_key = os.getenv('COINBASE_API_KEY')
api_secret = os.getenv('COINBASE_API_SECRET')

product_id = 'BTC-USD'

#####################################################
"continious market data for given time"
def market_data_subscription():
    def on_message(msg):
        print("------------------------------------")
        ### string format needs to be converted into dictionary
        print(msg)
        print('\n')

    def on_open():
        print("connection opened!")

    client = WSClient(api_key=api_key,
                    api_secret=api_secret,
                    on_message=on_message,
                    on_open=on_open)

    client.open()
    client.subscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])

    time.sleep(1)

    client.unsubscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])
    client.close()
#market_data_subscription()


#################################
"""aysnc functionality running forever  ctl+C to exit"""
def run_forever_market_data():

    def on_message(msg):
        "function that gets called when new data comes in"
        print('----------------------------------------------')
        print(msg)
        print('\n')

    client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, retry=False)

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
    connect_and_subscribe()

run_forever_market_data()