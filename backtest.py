import os
import pandas as pd
import utils
import datetime as dt
import wrapper
import numpy as np
from coinbase.rest import RESTClient
from strategies.strategy import Strategy
from strategies.efratio import EFratio
from strategies.vwap import Vwap
from strategies.rsi import RSI
from strategies.atr import ATR
from strategies.combined_strategy import Combined_Strategy
from log import LinkedList
from hyper import Hyper
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
import sqlite3


api_key = os.getenv('API_ENV_KEY') #API_ENV_KEY | COINBASE_API_KEY
api_secret = os.getenv('API_SECRET_ENV_KEY') #API_SECRET_ENV_KEY | COINBASE_API_SECRET
sandbox_key = os.getenv('SANDBOX_KEY')
sandbox_rest_url = "https://api-public.sandbox.exchange.coinbase.com"

client = RESTClient(api_key=api_key, api_secret=api_secret)


symbol = 'BTC-USD'
granularity = 'ONE_MINUTE'

def test_multiple_strategy():
    logbook = LinkedList()
    df_dict = utils.get_historical_from_db()

    for df in df_dict.values():
        rsi_vwap = Combined_Strategy(df, RSI, Vwap)
        rsi_vwap.generate_combined_signals()
        rsi_vwap.graph()

        # rsi = RSI(df)
        # rsi.custom_indicator(df.close)
        # rsi.graph()

        # vwap = Vwap(df)
        # vwap.custom_indicator(df.close)
        # vwap.graph()

        combined_pf = rsi_vwap.generate_backtest()
        logbook.insert_beginning(combined_pf)



#test_multiple_strategy()

def run_basic_backtest():
    timestamps = wrapper.get_unix_times(granularity=granularity, days=4)

    df = wrapper.get_candles(client=client,
                        symbol=symbol,
                        timestamps=timestamps,
                        granularity=granularity)

    strat = RSI(df=df)
    
    strat.custom_indicator(close=strat.close,
                           rsi_window=14,
                           buy_threshold=20,
                           sell_threshold=70)
    strat.graph()
    pf = strat.generate_backtest()
    for i in dir(pf):
        print(i)
    print('------------------------------------\n')
    print(pf.stats())


    # fig = pf.plot(subplots = [
    # 'orders',
    # 'trade_pnl',
    # 'cum_returns',
    # 'drawdowns',
    # 'underwater',
    # 'gross_exposure'])
    # fig.show()

    #print(stats)
run_basic_backtest()




def run_hyper():
    timestamps = wrapper.get_unix_times(granularity=granularity, days=4)

    df = wrapper.get_candles(client=client,
                     symbol=symbol,
                     timestamps=timestamps,
                     granularity=granularity)
    
    strat = EFratio(df)

    hyper = Hyper(strategy_object=strat,
                  close=strat.close,
                  efratio_window=np.arange(6, 12, step=3),
                  ef_threshold_buy=np.arange(0.1, 1, step=.3),
                  ef_threshold_sell=np.arange(-1, -0.1, step=.3))
    #print(hyper.returns.to_string())
    #print(type(hyper.returns))
    utils.export_hyper_to_db(hyper.returns, symbol, granularity, strat)

    #print(f"The maximum return was {hyper.returns.max()}\nefratio window: {hyper.returns.idxmax()[0]}\nef threshoold buy: {hyper.returns.idxmax()[1]}\nef threshold sell: {hyper.returns.idxmax()[2]}")
#run_hyper()