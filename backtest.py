import os
import pandas as pd
import utils
import datetime as dt
import wrapper
import numpy as np
import database_interaction
from coinbase.rest import RESTClient
from strategies.strategy import Strategy
from strategies.efratio import EFratio
from strategies.vwap import Vwap
from strategies.rsi import RSI
from strategies.atr import ATR
from strategies.macd import MACD
from strategies.kama import Kama
from strategies.combined_strategy import Combined_Strategy
from log import LinkedList
from hyper import Hyper
#pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)


api_key = os.getenv('API_ENV_KEY') #API_ENV_KEY | COINBASE_API_KEY
api_secret = os.getenv('API_SECRET_ENV_KEY') #API_SECRET_ENV_KEY | COINBASE_API_SECRET
sandbox_key = os.getenv('SANDBOX_KEY')
sandbox_rest_url = "https://api-public.sandbox.exchange.coinbase.com"

client = RESTClient(api_key=api_key, api_secret=api_secret)


symbols = ['BTC-USD', 'ETH-USD', 'MATH-USD']
symbol = ['BTC-USD']
granularity = 'THIRTY_MINUTE'

def test_multiple_strategy():
    logbook = LinkedList()
    df_dict = database_interaction.get_historical_from_db(granularity=granularity, symbols=symbols)


    for symbol, df in df_dict.items():
        current_dict_df = {symbol:df}

        combined_strat = Combined_Strategy(current_dict_df, RSI, Kama)
        combined_strat.generate_combined_signals()
        combined_strat.graph()
        combined_strat.generate_backtest()

        logbook.insert_beginning(combined_strat)
    
    logbook.export_multiple_to_db(granularity=granularity)

#test_multiple_strategy()


def run_basic_backtest():

    dict_df = database_interaction.get_historical_from_db(granularity=granularity,
                                                          symbols=symbol,
                                                          num_days=30)
    for key, value in dict_df.items():
        current_dict = {key : value}
        #current_dict = utils.heikin_ashi_transform(current_dict)
        
        strat = RSI(dict_df=current_dict)
        
        strat.custom_indicator(rsi_window=53, buy_threshold=38, sell_threshold=64)
        strat.graph()
        strat.generate_backtest()
        pf = strat.portfolio


        utils.export_backtest_to_db(object=strat,
                                    granularity=granularity)


        fig = pf.plot(subplots = [
        'orders',
        'trade_pnl',
        'cum_returns',
        'drawdowns',
        'underwater',
        'gross_exposure'])
        fig.show()

        print(pf.stats())
run_basic_backtest()




def run_hyper():
    dict_df = database_interaction.get_historical_from_db(granularity=granularity,
                                                          symbols=symbol,
                                                          num_days=30)

    #dict_df = utils.heikin_ashi_transform(dict_df)
    
    
    strat = RSI(dict_df)
    strat.custom_indicator()

    hyper = Hyper(strategy_object=strat,
                  close=strat.close,
                  rsi_window=np.arange(5, 70, step=1),
                  buy_threshold=np.arange(4, 50, step=2),
                  sell_threshold=np.arange(60, 98, step=2))
    print(hyper.returns.to_string())
    #print(type(hyper.returns))
    fig = hyper.returns.vbt.volume(# this line is now volume for a 3D
        x_level = 'cust_rsi_window',
        y_level = 'cust_buy_threshold',
        z_level = 'cust_sell_threshold',
    )
    fig.show()
    utils.export_hyper_to_db(hyper.returns, strat, granularity)

    print(f"The maximum return was {hyper.returns.max()}\nrsi_window: {hyper.returns.idxmax()[0]}\nbuy_threshold: {hyper.returns.idxmax()[1]}\nsell_threshold: {hyper.returns.idxmax()[2]}")
#run_hyper()

