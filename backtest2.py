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
granularity = 'FIVE_MINUTE'



def run_basic_backtest():

    dict_df = database_interaction.get_historical_from_db(granularity=granularity,
                                                          symbols=symbol,
                                                          num_days=30)
    for key, value in dict_df.items():
        current_dict = {key : value}
        #current_dict = utils.heikin_ashi_transform(current_dict)
        
        strat = Kama(dict_df=current_dict)
        vwap = Vwap(dict_df=current_dict)
        vwap.custom_indicator()
        vwap.graph()
        
        strat.custom_indicator(fast_window=2, slow_window=30)
        strat.graph()
        strat.generate_backtest()
        pf = strat.portfolio


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
#run_basic_backtest()


