import os
import pandas as pd
import utils
import datetime as dt
import wrapper
import numpy as np
from coinbase.rest import RESTClient
from strategies.strategy import Strategy
from strategies.kama import KAMA_Strategy
from backtest import Backtest
from hyper import Hyper
from strategies.vwap import Vwap_Strategy
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
    timestamps = wrapper.get_unix_times(granularity=granularity, days=4)

    df = wrapper.get_candles(client=client,
                        product_id=product_id,
                        timestamps=timestamps,
                        granularity=granularity)
    ####### future to try and set index to date for graphing purposes ########
    #df.set_index('date', inplace=True)

    kama_strat = KAMA_Strategy(df,
                        ti_data=None) # fast ma data
                        #ti2_data=None) # slow ma data

    kama_strat.custom_indicator(close = kama_strat.close,
                                efratio_window=15,
                                ef_threshold_buy= 0.1,
                                ef_threshold_sell= -0.8)

    backtest = Backtest(kama_strat)
    backtest.graph_strat(ti_data_name = "KAMA")
                         #ti2_data_name = 'Slow MA')
    stats = backtest.generate_backtest()
    print(stats)
#run_backtest()


def run_hyper():
    timestamps = wrapper.get_unix_times(granularity=granularity, days=4)

    df = wrapper.get_candles(client=client,
                     product_id=product_id,
                     timestamps=timestamps,
                     granularity=granularity)
    
    kama_strat = KAMA_Strategy(df,
                        ti_data=None)
                        #ti2_data=None)

    hyper = Hyper(strategy_object=kama_strat,
                  close=kama_strat.close,
                  efratio_window=np.arange(6, 30, step=3),
                  ef_threshold_buy=np.arange(0.1, 1, step=.1),
                  ef_threshold_sell=np.arange(-1, -0.1, step=.1))
    
    print(hyper.returns.to_string())
    print(f"The maximum return was {hyper.returns.max()}\nefratio window: {hyper.returns.idxmax()[0]}\nef threshoold buy: {hyper.returns.idxmax()[1]}\nef threshold sell: {hyper.returns.idxmax()[2]}")
#run_hyper()

def test_vvwap():
    timestamps = wrapper.get_unix_times(granularity=granularity, days=4)

    df = wrapper.get_candles(client=client,
                     product_id=product_id,
                     timestamps=timestamps,
                     granularity=granularity)
    
    vvwap_strategy = Vwap_Strategy(df)

    
    vvwap_strategy.vwap()                
test_vvwap()

def download_historical_data():
    timestamps = wrapper.get_unix_times(granularity=granularity, days=90)
    df = wrapper.get_candles(client=client,
                        product_id=product_id,
                        timestamps=timestamps,
                        granularity=granularity)
    todays_date = str(dt.datetime.now().date())
    df.to_csv(path_or_buf=f"historical_data/{product_id}_{todays_date}.csv", sep=',')


#download_historical_data()




"""below will eventually be put in a Risk Analysis Class"""
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
    print(dict)
#get_portfolio_breakdown()

