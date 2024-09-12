import os
import asyncio
import pandas as pd
import utils
import asyncio
from coinbase.rest import RESTClient
from strategies.strategy import Strategy
from backtest import Backtest
from wrapper import get_candles, get_unix_times
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


api_key = os.getenv('API_ENV_KEY') #API_ENV_KEY | COINBASE_API_KEY
api_secret = os.getenv('API_SECRET_ENV_KEY') #API_SECRET_ENV_KEY | COINBASE_API_SECRET
sandbox_key = os.getenv('SANDBOX_KEY')
sandbox_rest_url = "https://api-public.sandbox.exchange.coinbase.com"

client = RESTClient(api_key=api_key, api_secret=api_secret)


product_id = 'BTC-USD'
granularity = 'ONE_MINUTE'


def run_backtest():
    timestamps = get_unix_times(granularity=granularity, days=3)

    df = get_candles(client=client,
                        product_id=product_id,
                        timestamps=timestamps,
                        granularity=granularity)

    ma_strat = Strategy(df,
                        param1_data=None, # fast ma data
                        param2_data=None) # slow ma data

    ma_strat.custom_indicator(fast_window=30, slow_window=80)

    backtest = Backtest(ma_strat)
    backtest.graph_strat(param1_data_name = "Fast MA",
                        param2_data_name = 'Slow MA')
    stats = backtest.generate_backtest()
    print(stats)
#run_backtest()


def get_product_book():
    """gets bids gets asks and time could eventually incorpoate into scanner"""

    dict = client.get_product_book(product_id=product_id, limit=10)
    df = utils.to_df(dict)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    print(df.columns)
#get_product_book()



def get_products(client, only_price = False):
    """lots of data in df to use in scanner such as volume, and change percentage"""

    pd.set_option('display.float_format', lambda x: '%.6f' % x)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    dict = client.get_products(get_all_products=True)
    df = utils.to_df(dict)
    if only_price:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[['product_id', 'price']].sort_values(by='price', ascending=False)
    return df



def get_best_bid_ask():
    """gets the best bid and ask"""

    dict = client.get_best_bid_ask(product_ids=[product_id])
    df = utils.to_df(dict)
    print(df.head())
#get_best_bid_ask()


def get_market_trades():
    """get the last market trades that have occured"""

    timestamps = get_unix_times(granularity=granularity)
    dict = client.get_market_trades(product_id=product_id, limit = 10, start=timestamps[0][1], end=timestamps[0][0])
    df = utils.to_df(dict)
    print(df.head())
#get_market_trades()

def get_portfolio_uuid():
    """gets portfolio data this returns the uuid which is needed for further portfolio data"""
    dict = client.get_portfolios() # only good data in this is the uuid
    uuid = dict['portfolios'][0]['uuid']
    return uuid

def get_portfolio_breakdown():
    """LOTS OF NESTED DICTIONARYS IN THIS ONE!! good information about portfolio metrics though"""
    # STILL NEED TO FINISH 
    indent = 0
    uuid = get_portfolio_uuid()
    dict = client.get_portfolio_breakdown(portfolio_uuid=uuid)
#get_portfolio_breakdown()

