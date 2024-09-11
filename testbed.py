import os
import pandas as pd
from coinbase.rest import RESTClient
from strategies.strategy import Strategy
from backtest import Backtest
from wrapper import get_candles, get_unix_times, get_products
import utils


api_key = os.getenv('COINBASE_API_KEY')
api_secret = os.getenv('COINBASE_API_SECRET')
sandbox_key = os.getenv('SANDBOX_KEY')
sandbox_rest_url = "https://api-public.sandbox.exchange.coinbase.com"

client = RESTClient(api_key=api_key, api_secret=api_secret)
product_id = 'BTC-USD'


def run_backtest():
    product_id = 'BTC-USD'
    granularity = 'ONE_MINUTE'
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


