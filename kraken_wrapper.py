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
        self.nonce_counter = 1

    def get_nonce(self):
        if self.nonce_counter > 14:
            self.conce_counter = 1
        base_nonce = int(time.time() * 10000)
        nonce = base_nonce + self.nonce_counter
        self.nonce_counter += 1
        return str(nonce)

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

    def get_extended_balance(self, symbol):
        """gets how much volume we have bought for the symbol passed"""
        symbol_map = {'XXBTZUSD':'XXBT',
                      'XETHZUSD': 'XETH',
                      'XDGUSD': 'XXDG',
                      'SHIBUSD': 'SHIB',
                      'AVAXUSD': 'AVAX',
                      'BCHUSD': 'BCH',
                      'LINKUSD': 'LINK',
                      'UNIUSD': 'UNI',
                      'XLTCZUSD': 'XLTC',
                      'XXLMZUSD': 'XXLM',
                      'XETCZUSD': 'XETC',
                      'AAVEUSD': 'AAVE',
                      'XTZUSD': 'XTZ',
                      'COMPUSD': 'COMP'}
        url_path = '/0/private/BalanceEx'
        url = self.base_url + url_path
        nonce = self.get_nonce()
        data = {'nonce': nonce}

        self.get_kraken_signature(urlpath=url_path,data=data, secret=self.api_secret)

        response = requests.request("POST", url, headers=self.headers, data=data)

        data = response.json()
        all_held_data = data.get('result',{})
        symbol = symbol_map[symbol]
        for pair, amount in all_held_data.items():
            if symbol == pair:
                current_balance = amount['balance']
        return current_balance



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
        nonce = self.get_nonce()
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
        nonce = self.get_nonce()

        data = {'nonce': nonce,
                'asset': 'ZUSD'}

        self.get_kraken_signature(urlpath, data, self.api_secret)

        response = requests.request("POST", url, headers=self.headers, data=data)
        response_data = response.json()
        print(response_data)

        return float(response_data['result']['eb'])

    def any_open_orders(self, pickle=False):
        urlpath = '/0/private/OpenOrders'
        url = self.base_url + urlpath
        nonce = self.get_nonce()

        data = {'nonce': nonce,
                'trades': True}

        self.get_kraken_signature(urlpath, data, self.api_secret)

        response = requests.request("POST", url, headers=self.headers, data=data)
        response_data = response.json()
        if pickle:
            pickling.to_pickle('open_orders', response_data)
        open_data = response_data['result']['open']

        #returns False if theres no open orders
        if response_data['result']['open']=={}:
            return False
        else:
            #returns True if there are open orders
            return True
        
        # print(response_data['result']['open']=={})
        # print('-------------------------------------------------------------------')
        # for id in open_data:
        #     print(open_data)
        #     print('------------------------------------')
        #     print(open_data[id])
        #     print('---------------------')
        #     print(open_data[id]['descr'])
        #     print('*************************')
        # #print(f'Open Orders: {response.text}')


    def get_open_postions(self):
        urlpath = '/0/private/OpenPositions'
        url = self.base_url + urlpath
        nonce = self.get_nonce()

        data = {'nonce': nonce,
                'trades': True,
                'txid': 'string',
                'docalcs': False,
                'consolidation': 'market'
            }
        
        self.get_kraken_signature(urlpath=urlpath, data=data, secret=self.api_secret)
        response = requests.request("POST", url, headers=self.headers, data=data)
        print(response.text)

    def add_order(self, type_of_order, symbol, volume, price, pickle=True):
        if type_of_order not in ['buy', 'sell']:
            print('needs to be "buy" or "sell"')
        url_path = '/0/private/AddOrder'
        url = self.base_url + url_path
        nonce = self.get_nonce()


        data = {"nonce": nonce,
                'ordertype': 'limit',
                'type': type_of_order,
                'volume': volume,
                'pair': symbol,
                'price': price}
        
        self.get_kraken_signature(urlpath=url_path, data=data, secret=self.api_secret)

        response = requests.request("POST",url, headers=self.headers, data=data)
        response_data = response.json()
        if pickle:
            pickling.to_pickle(f'{type_of_order}_order_{symbol}', response_data)
        return response_data

    def edit_order(self, order_id, symbol, volume, price, pickle=False):
        url_path = '/0/private/EditOrder'
        url = self.base_url + url_path 
        data = {
            'nonce': self.get_nonce(),
            'pair': symbol,
            'txid': order_id,
            'volume': volume,
            'price':price
        }

        self.get_kraken_signature(
            urlpath = url_path,
            data = data,
            secret=self.api_secret)
        
        response = requests.request("POST",url=url, headers=self.headers, data=data)
        response_data = response.json()
        if pickle:
            pickling.to_pickle(f'updated_order_{symbol}', response_data)
        print('order has been updated')
        print(response_data)


    def get_closed_orders(self):
        urlpath = '/0/private/ClosedOrders'
        url = self.base_url + urlpath
        nonce = self.get_nonce()
        data = {'nonce': nonce,
                'trades': True}
        
        self.get_kraken_signature(urlpath, data, self.api_secret)
        response = requests.request("POST", url, headers=self.headers, data=data)
        print(response.text)

    def get_trade_volume(self):
            url_path = '/0/private/TradeVolume'
            url = self.base_url + url_path
            nonce = self.get_nonce()
            data = {'nonce': nonce,
                    'pair': "BTC/USD"
                }
            
            self.get_kraken_signature(url_path, data, self.api_secret)
            response = requests.request("POST", url, headers=self.headers, data=data)

            print(f'Volume: {response.text}')

    def get_order_book(self, symbol):
        url_path = '/0/public/Depth'
        query = f'?pair={symbol}'
        url_path += query
        url = self.base_url + url_path
        #nonce = self.get_nonce()
        data = {}

        self.get_kraken_signature(urlpath=url_path, data=data, secret=self.api_secret)

        response = requests.request('GET', url=url, headers=self.headers, data=data)
        print(response.text)

    def get_recent_spreads(self, symbol, type_of_order):
        url_path = '/0/public/Spread'
        queary = f'?pair={symbol}'
        url_path += queary
        url = self.base_url + url_path
        data = {}

        self.get_kraken_signature(url_path,self.headers,data)
        response = requests.request(
            "GET",
            url= url,
            headers = self.headers,
            data = data)
        data = response.json()
        key = list(data['result'].keys())[0]
        current_spread = data['result'][key][-1]
        if type_of_order == 'sell':
            new_price = current_spread[1]
        elif type_of_order == 'buy':
            new_price = current_spread[2]
        return new_price
        




# testing_kraken = Kraken()
# testing_kraken.get_trade_balance("ZUSD")
# testing_kraken.get_account_balance()
# testing_kraken.get_open_orders()
# testing_kraken.get_open_postions()