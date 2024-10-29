import os
import pandas as pd
import datetime as dt
import sys
import requests
import utils
import time
import json

class Kraken():

    def __init__(self, interval: str=None):
        self.api_key = os.getenv('API_KEY_KRAKEN') #API_ENV_KEY | KRAKEN
        self.api_secret = os.getenv('API_PRIVATE_KEY_KRAKEN') #API_SECRET_ENV_KEY | KRAKEN
        self.base_url = 'https://api.kraken.com/0'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'API-Key': self.api_key,
            'API-Sign': self.api_secret
        }

        self.interval_map = {
            "ONE_MINUTE": 1,
            "FIVE_MINUTE": 5,
            "FIFTEEN_MINUTE": 15,
            "THIRTY_MINUTE": 30,
            "ONE_HOUR": 60,
            "FOUR_HOUR": 240,
            "ONE_DAY": 1440,
            "ONE_WEEK": 10080,
            "FIFTEEN_DAYS": 21600
        }
        if interval == None:
            self.interval = 'ONE_MINUTE'
        else:
            self.interval = interval
        if self.interval not in self.interval_map.keys():
            print(f'interval must be one of the following: {[k for k in self.interval_map.keys()]}')
            sys.exit()

        self.all_products = self.get_tradable_asset_pairs()
        self.time_to_wait = self.interval_map[self.interval] * 60


    def get_historical_data(self,pair: str, days_ago=None):
        if days_ago is not None:
            now = dt.datetime.now()
            since = now - dt.timedelta(days=days_ago)
            since = int(since.timestamp())
        else:
            since = days_ago

        function_url = self.base_url + '/public/OHLC?'
            
        parameters = '&'.join([f'pair={pair}' if pair else '',
                            f'interval={self.interval_map[self.interval]}' if self.interval else '',
                            f'since={since}' if since else '']).strip('&')
        
        url = function_url + parameters
        print(url)
        
        payload = {}
        response = requests.request("GET", url, headers=self.headers, data=payload)

        data = response.json()
        error = data.get("error",[])
        result = data.get('result',{})
        #print(result.keys())
        symbol = list(result.keys())[0]
        symbol_data = result[symbol]


        df = pd.DataFrame(symbol_data, columns=["date", "open", "high", "low", "close", "vwap", "volume", "count"])
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        dict_df = {symbol: df}
        return dict_df


    def get_tradable_asset_pairs(self):
        url = self.base_url + '/public/AssetPairs'
        payload = {}

        response = requests.request("GET", url, headers=self.headers,data=payload )

        data = response.json()
        result = data.get('result', {})
        self.symbols_to_trade = list(result.keys())
        return self.symbols_to_trade
    
    def get_account_balance(self):
        print('getting account balance')
        url = self.base_url + '/private/Balance'

        payload = json.dumps({
            "nonce": str(int(time.time()* 1000))})
        
        response = requests.request("POST", url, headers=self.headers, data=payload)
        print(response)

        print(response.text)



            

