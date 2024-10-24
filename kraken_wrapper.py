import os
import pandas as pd
import datetime as dt
import sys
import requests

class Kraken():

    def __init__(self):
        self.api_key = os.getenv('API_KEY_KRAKEN') #API_ENV_KEY | KRAKEN
        self.api_secret = os.getenv('API_PRIVATE_KEY_KRAKEN') #API_SECRET_ENV_KEY | KRAKEN
        self.base_url = 'https://api.kraken.com/0'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'API-Key': self.api_key,
            'API-Sign': self.api_secret
        }

        self.intervals = [1,5,15,30,60,240,1440,10080,21600]


    def get_historical_data(self,pair=None, interval=None, since=None):
        function_url = self.base_url + '/public/OHLC?'

        if interval not in self.intervals:
            print(f'interval must be one of the following: {[str(x) for x in self.intervals]}')
            sys.exit()
            
        parameters = '&'.join([f'pair={pair}' if pair else '',
                            f'interval={interval}' if interval else '',
                            f'since={since}' if since else '']).strip('&')
        
        url = function_url + parameters
        print(url)
        
        payload = {}
        response = requests.request("GET", url, headers=self.headers, data=payload)

        data = response.json()
        error = data.get("error",[])
        result = data.get('result',{})

        symbol = list(result.keys())[0]
        symbol_data = result[symbol]


        df = pd.DataFrame(symbol_data, columns=["date", "open", "high", "low", "close", "vwap", "volume", "count"])
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        dict_df = {symbol: df}
        return dict_df


