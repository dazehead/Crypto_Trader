import time
import os
import re
from coinbase.websocket import WSClient, WSClientConnectionClosedException
from utils import to_df

api_key = os.getenv('API_ENV_KEY')
api_secret =  os.getenv('API_SECRET_ENV_KEY')

product_id = 'BTC-USD'

#####################################################
"Continuous market data for given time"
def market_data_subscription():
    def on_message(msg):
        print("------------------------------------")
        
        # Print the raw message received
        print("Raw message:", msg)
        
        # Example regex patterns to extract key data from msg
        price_pattern = r'"price"\s*:\s*"(\d+\.\d+)"'   # Regex for extracting price (decimal number)
        time_pattern = r'"time"\s*:\s*"([^"]+)"'        # Regex for extracting time (string)
        volume_pattern = r'"volume"\s*:\s*"(\d+\.\d+)"' # Regex for extracting volume (decimal number)

        # Extract price
        price_match = re.search(price_pattern, msg)
        if price_match:
            price = price_match.group(1)
            print("Extracted Price:", price)
        else:
            print("Price not found.")

        # Extract time
        time_match = re.search(time_pattern, msg)
        if time_match:
            timestamp = time_match.group(1)
            print("Extracted Timestamp:", timestamp)
        else:
            print("Timestamp not found.")
        
        # Extract volume (if available)
        volume_match = re.search(volume_pattern, msg)
        if volume_match:
            volume = volume_match.group(1)
            print("Extracted Volume:", volume)
        else:
            print("Volume not found.")
        
        print('\n')

    def on_open():
        print("Connection opened!")

    client = WSClient(api_key=api_key,
                    api_secret=api_secret,
                    on_message=on_message,
                    on_open=on_open)

    client.open()
    client.subscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])

    time.sleep(1)

    client.unsubscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])
    client.close()

market_data_subscription()


#################################
"""Async functionality running forever  ctl+C to exit"""
def run_forever_market_data():

    def on_message(msg):
        "Function that gets called when new data comes in"
        print('----------------------------------------------')
        
        # Regex pattern to extract key fields from the string message
        price_pattern = r'"price"\s*:\s*"(\d+\.\d+)"'    # Extracts price
        time_pattern = r'"time"\s*:\s*"([^"]+)"'         # Extracts time
        volume_pattern = r'"volume"\s*:\s*"(\d+\.\d+)"'  # Extracts volume

        # Extract price
        price_match = re.search(price_pattern, msg)
        if price_match:
            price = price_match.group(1)
            print(f"Extracted Price: {price}")
        else:
            print("Price not found.")

        # Extract time
        time_match = re.search(time_pattern, msg)
        if time_match:
            timestamp = time_match.group(1)
            print(f"Extracted Timestamp: {timestamp}")
        else:
            print("Timestamp not found.")
        
        # Extract volume
        volume_match = re.search(volume_pattern, msg)
        if volume_match:
            volume = volume_match.group(1)
            print(f"Extracted Volume: {volume}")
        else:
            print("Volume not found.")

        print('----------------------------------------------\n')

    client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, retry=False)

    def connect_and_subscribe():
        "Function to connect, subscribe and then reconnect after 20 seconds"
        try:
            client.open()
            client.subscribe(product_ids=[product_id], channels=['candles', 'heartbeats'])
            client.run_forever_with_exception_check()
        except WSClientConnectionClosedException as e:
            print("Connection closed! Sleeping for 20 seconds before reconnecting...")
            time.sleep(20)
            connect_and_subscribe()
    
    connect_and_subscribe()

#run_forever_market_data()
