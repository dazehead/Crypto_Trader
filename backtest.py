import os
import pandas as pd
import utils
import datetime as dt
import wrapper
import numpy as np
import database_interaction
from coinbase.rest import RESTClient
from strategies.strategy import Strategy
from strategies.single.efratio import EFratio
from strategies.single.vwap import Vwap
from strategies.single.rsi import RSI
from strategies.single.atr import ATR
from strategies.single.macd import MACD
from strategies.single.kama import Kama
from strategies.single.adx import ADX
from strategies.double.rsi_adx import RSI_ADX
from strategies.combined_strategy import Combined_Strategy
from risk import Risk_Handler
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
product = ['BTC-USD']
granularity = 'FIVE_MINUTE'

def test_multiple_strategy():
    logbook = LinkedList()
    df_dict = database_interaction.get_historical_from_db(granularity=granularity, symbols=product, num_days=40)


    for symbol, df in df_dict.items():
        current_dict_df = {symbol:df}

        combined_strat = Combined_Strategy(current_dict_df, RSI, ADX)
        combined_strat.generate_combined_signals()
        combined_strat.graph()
        combined_strat.generate_backtest()
        print(combined_strat.portfolio.stats())


    #     logbook.insert_beginning(combined_strat)
    
    # logbook.export_multiple_pf_to_db()

#test_multiple_strategy()


def run_basic_backtest():

    dict_df = database_interaction.get_historical_from_db(granularity=granularity,
                                                          symbols=product,
                                                          num_days=300)
    for key, value in dict_df.items():
        current_dict = {key : value}
        #current_dict = utils.heikin_ashi_transform(current_dict)
        risk = Risk_Handler()
        
        strat = RSI_ADX(
            dict_df=current_dict,
            with_sizing=True,
            risk_object=risk)
        
        strat.custom_indicator()
        strat.graph()
        strat.generate_backtest()
        #strat.from_orders(init_cash=100)
        pf = strat.portfolio
        print(pf.stats())


        # utils.export_backtest_to_db(object=strat,
        #                             granularity=granularity)


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
                                                          symbols=product,
                                                          num_days=300)

    #dict_df = utils.heikin_ashi_transform(dict_df)
    
    
    strat = RSI_ADX(dict_df)
    #strat.custom_indicator()

    hyper = Hyper(strategy_object=strat,
                  close=strat.close,
                  rsi_window=np.arange(10, 30, step=5),
                  buy_threshold=np.arange(5, 51, step=5),
                  sell_threshold = np.arange(50, 96, step=5),
                  adx_buy_threshold = np.arange(20, 81, step=10),
                  adx_time_period=np.arange(10, 30, step=5))
    #print(hyper.returns.to_string())
    #print(type(hyper.returns))

    # fig = hyper.returns.vbt.volume(# this line is now volume for a 3D
    #     x_level = 'cust_fast_window',
    #     y_level = 'cust_slow_window',
    #     z_level = 'cust_efrato_window',
    # )

    # fig = hyper.returns.vbt.heatmap(
    # x_level = 'cust_fast_window',
    # y_level = 'cust_slow_window')
    #fig.show()
    #utils.export_hyper_to_db(hyper.returns, strat, granularity)

    print(f"The maximum return was {hyper.returns.max()}")
    params = ['rsi_window','buy_threshold','sell_threshold','adx_buy_threshold','adx_time_period']
    for i,value in enumerate(params):
        print(f'{value}: {hyper.returns.idxmax()[i]}')

#run_hyper()

