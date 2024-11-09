import os
import pandas as pd
import utils
import datetime as dt
import coinbase_wrapper
import numpy as np
import database_interaction
import time
import gc
import gc
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


symbols = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SHIB-USD', 'AVAX-USD', 'BCH-USD', 'LINK-USD', 'UNI-USD', 'LTC-USD', 'XLM-USD', 'ETC-USD', 'AAVE-USD', 'XTZ-USD', 'COMP-USD']
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
                                                          symbols=symbols,
                                                          num_days=1)
    for key, value in dict_df.items():
        current_dict = {key : value}
        print(key)
        #current_dict = utils.heikin_ashi_transform(current_dict)
        # risk = Risk_Handler()
        
        # strat = RSI_ADX(
        #     dict_df=current_dict,
        #     with_sizing=True,
        #     risk_object=risk)
        
        # strat.custom_indicator()
        # strat.graph()
        # strat.generate_backtest()
        # pf = strat.portfolio
        # print(pf.stats())



        # database_interaction.export_backtest_to_db(object=strat)


        # fig = pf.plot(subplots = [
        # 'orders',
        # 'trade_pnl',
        # 'cum_returns',
        # 'drawdowns',
        # 'underwater',
        # 'gross_exposure'])
        # fig.show()

        # print(pf.stats())
#run_basic_backtest()




def run_hyper():
    dict_df = database_interaction.get_historical_from_db(granularity=granularity,
                                                        symbols=symbols,
                                                        num_days=100)
    print(f'...Running hyper on {len(symbols)} symbols')

    #dict_df = utils.heikin_ashi_transform(dict_df)

    start_time = time.time()
    for i,items in enumerate(dict_df.items()):
        key, value = items
        current_dict = {key:value}
        
        strat = RSI_ADX(current_dict)

        hyper = Hyper(
            strategy_object=strat,
            close=strat.close,
            rsi_window=np.arange(10, 30, step=5),
            buy_threshold=np.arange(5, 51, step=5),
            sell_threshold = np.arange(50, 96, step=5),
            adx_buy_threshold = np.arange(20, 81, step=10),
            adx_time_period=np.arange(10, 30, step=5))

        database_interaction.export_hyper_to_db(
            strategy=strat,
            hyper=hyper)
        
        utils.progress_bar_with_eta(
            progress=i,
            data=dict_df.keys(),
            start_time=start_time)
        del hyper
        gc.collect()
        
        # fig = hyper.returns.vbt.volume(# this line is now volume for a 3D
        #     x_level = 'cust_fast_window',
        #     y_level = 'cust_slow_window',
        #     z_level = 'cust_efrato_window',
        # )

            # fig = hyper.returns.vbt.heatmap(
            # x_level = 'cust_fast_window',
            # y_level = 'cust_slow_window')
            # fig.show()
run_hyper()

