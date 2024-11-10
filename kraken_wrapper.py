import os
import pandas as pd
import datetime as dt
import sys
import requests
import utils
import time
import json
import urllib.parse
import hashlib
import hmac
import base64
import database_interaction
import pickling

class Kraken():

    def __init__(self, granularity: str=None):
        self.api_key = os.getenv('API_KEY_KRAKEN') #API_ENV_KEY | KRAKEN
        self.api_secret = os.getenv('API_PRIVATE_KEY_KRAKEN') #API_SECRET_ENV_KEY | KRAKEN
        self.base_url = 'https://api.kraken.com'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'API-Key': self.api_key,
            'API-Sign': self.api_secret
        }

        self.granularity_map = {
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
        if granularity == None:
            self.granularity = 'ONE_MINUTE'
        else:
            self.granularity = granularity
        if self.granularity not in self.granularity_map.keys():
            print(f'granularity must be one of the following: {[k for k in self.granularity_map.keys()]}')
            sys.exit()

        self.all_products = self.get_tradable_asset_pairs()
        self.time_to_wait = self.granularity_map[self.granularity] * 60


    def get_kraken_signature(self, urlpath, data, secret):
        if 'public' in urlpath:
            self.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'API-Key': self.api_key,
                'API-Sign': self.api_secret
            }
            return
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode('utf-8')
        message = urlpath.encode('utf-8') + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())

        self.headers['API-Sign'] = sigdigest.decode()

        if 'private' in urlpath:
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8'
        return #sigdigest.decode()

    def get_historical_data(self,pair: str, days_ago=None):
        """days_ago using kraken for some reason only gets 1 days worth datat"""
        if days_ago is not None:
            now = dt.datetime.now()
            since = now - dt.timedelta(days=days_ago)
            since = int(since.timestamp())
        else:
            since = days_ago

        function_url = self.base_url + '/0/public/OHLC?'
            
        parameters = '&'.join([f'pair={pair}' if pair else '',
                            f'interval={self.granularity_map[self.granularity]}' if self.granularity else '',
                            f'since={since}' if since else '']).strip('&')
        
        url = function_url + parameters
        
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


    def get_tradable_asset_pairs(self):
        url = self.base_url + '/0/public/AssetPairs'
        payload = {}

        response = requests.request("GET", url, headers=self.headers,data=payload )

        data = response.json()
        result = data.get('result', {})
        self.symbols_to_trade = list(result.keys())
        return self.symbols_to_trade
    
    def get_account_balance(self):
        """This function does not get our actual account blance it is get_trade_balance that get the portfolio balanace"""
        urlpath = '/0/private/Balance'
        url = self.base_url + urlpath
        nonce = str(int(time.time() * 1000))
        data = {'nonce': nonce}

        # Compute signature
        self.get_kraken_signature(urlpath, data, self.api_secret)
        response = requests.post(url, headers=self.headers, data=data)

        response_data = response.json()
        if response_data['error']:
            print(f"Error: {response_data['error']}")
        else:
            balance = response_data['result']
            zusd_balance = balance.get('ZUSD', '0')
            return float(zusd_balance)

    def get_trade_balance(self):
        """note this can also get unrealized profit/loss"""
        urlpath = '/0/private/TradeBalance'
        url = self.base_url + urlpath
        nonce = str(int(time.time() * 1000))

        data = {'nonce': nonce,
                'asset': 'ZUSD'}

        self.get_kraken_signature(urlpath, data, self.api_secret)

        response = requests.request("POST", url, headers=self.headers, data=data)
        response_data = response.json()
        print(response_data)

        return float(response_data['result']['eb'])

    def get_open_orders(self):
        urlpath = '/0/private/OpenOrders'
        url = self.base_url + urlpath
        nonce = str(int(time.time() * 1000))

        data = {'nonce': nonce,
                'trades': True}

        self.get_kraken_signature(urlpath, data, self.api_secret)

        response = requests.request("POST", url, headers=self.headers, data=data)
        response_data = response.json()
        print(response_data['result']['open'])

        print(f'Open Orders: {response.text}')


    def get_open_postions(self):
        urlpath = '/0/private/OpenPositions'
        url = self.base_url + urlpath
        nonce = str(int(time.time() * 1000))

        data = {'nonce': nonce,
                'trades': True,
                'txid': 'string',
                'docalcs': False,
                'consolidation': 'market'
            }
        
        self.get_kraken_signature(urlpath=urlpath, data=data, secret=self.api_secret)
        response = requests.request("POST", url, headers=self.headers, data=data)
        print(response.text)

    def add_order(self, type_of_order, symbol, volume ,pickle=True):
        if type_of_order not in ['buy', 'sell']:
            print('needs to be "buy" or "sell"')
        urlpath = '/0/private/AddOrder'
        url = self.base_url + urlpath
        nonce = str(int(time.time()) * 1000)

        data = {"nonce": nonce,
                'ordertype': 'market',
                'type': type_of_order,
                'volume': volume,
                'pair': symbol}
                #'price': price,
                #'cl_ord_id': "generated order id from database"}
        
        self.get_kraken_signature(urlpath=urlpath, data=data, secret=self.api_secret)

        response = requests.request("POST",url, headers=self.headers, data=data)
        response_data = response.json()
        if pickle:
            pickling.to_pickle(f'{type_of_order}_order', response_data)
        return response_data


    def get_closed_orders(self):
        urlpath = '/0/private/ClosedOrders'
        url = self.base_url + urlpath
        nonce = str(int(time.time() * 1000))
        data = {'nonce': nonce,
                'trades': True}
        
        self.get_kraken_signature(urlpath, data, self.api_secret)
        response = requests.request("POST", url, headers=self.headers, data=data)
        print(response.text)

    def get_trade_volume(self):
            urlpath = '/0/private/TradeVolume'
            url = self.base_url + urlpath
            nonce = str(int(time.time() * 1000))
            data = {'nonce': nonce,
                    'pair': "BTC/USD"
                }
            
            self.get_kraken_signature(urlpath, data, self.api_secret)
            response = requests.request("POST", url, headers=self.headers, data=data)

            print(f'Volume: {response.text}')

    def get_order_book(self):
        url_path = '/0/public/Depth'
        url = self.base_url + url_path
        nonce = str(int(time.time() * 1000))
        data = {}

        self.get_kraken_signature(urlpath=url_path, data=data, secret=self.api_secret)

        response = requests.request('GET', url=url, headers=self.headers, data=data)
        print(response.text)

# testing_kraken = Kraken()
# testing_kraken.get_trade_balance("ZUSD")
# testing_kraken.get_account_balance()
# testing_kraken.get_open_orders()
# testing_kraken.get_open_postions()