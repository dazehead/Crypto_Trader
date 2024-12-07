import os
import pandas as pd
import core.utils as utils
import datetime as dt
import coinbase_wrapper
import numpy as np
import core.database_interaction as database_interaction
import time
import gc
import gc
from coinbase.rest import RESTClient
from core.strategies.strategy import Strategy
from core.strategies.single.efratio import EFratio
from core.strategies.single.vwap import Vwap
from core.strategies.single.rsi import RSI
from core.strategies.single.atr import ATR
from core.strategies.single.macd import MACD
from core.strategies.single.kama import Kama
from core.strategies.single.adx import ADX
from core.strategies.double.rsi_adx import RSI_ADX
from core.strategies.combined_strategy import Combined_Strategy
from core.strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
from core.risk import Risk_Handler
from core.log import LinkedList
from core.hyper import Hyper
#pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)



class Backtest():
    def __init__(self, symbols=None, granularities=None, chosen_strat=None, num_days=None, ):
        if symbols:
            self.symbols = symbols
        else:
            self.symbols = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SHIB-USD', 'AVAX-USD', 'BCH-USD', 'LINK-USD', 'UNI-USD', 'LTC-USD', 'XLM-USD', 'ETC-USD', 'AAVE-USD', 'XTZ-USD', 'COMP-USD']

        if granularities:
            self.granularites = granularities
        else:
            self.granularites = ['ONE_MINUTE','FIVE_MINUTE','FIFTEEN_MINUTE','THIRTY_MINUTE','ONE_HOUR','TWO_HOUR','SIX_HOUR','ONE_DAY']
        
        if chosen_strat:
            if len(chosen_strat) > 1:
                self.strat1 = chosen_strat[0]
                self.strat2 = chosen_strat[1]
            else:
                self.strat1 = chosen_strat
        if num_days:
            self.num_days = num_days
        else:
            self.num_days = 30


        self.product = ['BTC-USD']
        self.granularity = 'ONE_MINUTE'
        self.num_days = num_days
        


    def test_multiple_strategy(self):
        logbook = LinkedList()
        df_dict = database_interaction.get_historical_from_db(granularity=self.granularity, symbols=self.symbols, num_days=50)


        for symbol, df in df_dict.items():
            current_dict_df = {symbol:df}

            combined_strat = Combined_Strategy(current_dict_df, RSI, ADX)
            combined_strat.generate_combined_signals()
            combined_strat.graph()
            combined_strat.generate_backtest()
            print(combined_strat.portfolio.stats())



            logbook.insert_beginning(combined_strat)
        
        logbook.export_multiple_pf_to_db()



    def run_basic_backtest(self):
        # for granularity in granularites:
        #     if granularity == 'ONE_MINUTE':
        #         days = 50
        #     elif granularity == 'FIVE_MINUTE':
        #         days = 150
        #     else:
        #         days = 365

        dict_df = database_interaction.get_historical_from_db(granularity='THIRTY_MINUTE',
                                                            symbols=self.symbols,
                                                            num_days=365)
        for key, value in dict_df.items():
            current_dict = {key : value}

            #current_dict = utils.heikin_ashi_transform(current_dict)
            risk = Risk_Handler()
            
            strat = RSI_ADX(
                dict_df=current_dict,
                risk_object=risk,
                with_sizing=True
            )

            params = database_interaction.get_best_params(
                strategy_object=strat, 
                best_of_all_granularities=True,
                minimum_trades=3)
            print(params)

            strat.custom_indicator(None, *params)
            strat.graph()
            strat.generate_backtest()
            pf = strat.portfolio
            print(pf.stats())

            fig = pf.plot(subplots = [
            'orders',
            'trade_pnl',
            'cum_returns',
            'drawdowns',
            'underwater',
            'gross_exposure'])
            fig.update_layout(
                title={
                    'text': f"{strat.__class__.__name__} for {strat.symbol} on {strat.granularity} timeframe",  # Replace with your desired title
                    'x': 0.5,  # Centers the title
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                margin={
                    't': 100  # Adjust the top margin to create space for the title
                }
            )
            fig.show()

    def run_hyper(self):
        risk = Risk_Handler()
        for granularity in self.granularites:
            if granularity == 'ONE_MINUTE':
                days = 25
            elif granularity == 'FIVE_MINUTE':
                days = 100
            elif granularity == 'FIFTEEN_MINUTE':
                days = 250
            else:
                days = 365
            dict_df = database_interaction.get_historical_from_db(granularity=granularity,
                                                                symbols=self.symbols,
                                                                num_days=days)
            print(f'...Running hyper on {len(self.symbols)} symbols')

            #dict_df = utils.heikin_ashi_transform(dict_df)

            start_time = time.time()
            for i,items in enumerate(dict_df.items()):
                key, value = items
                current_dict = {key:value}
                
                strat = RSI_ADX(current_dict, risk_object=risk, with_sizing=True)

                hyper = Hyper(
                    strategy_object=strat,
                    close=strat.close,
                    rsi_window=np.arange(10, 30, step=15),
                    buy_threshold=np.arange(5, 50, step=15),
                    sell_threshold = np.arange(50, 95, step=15),
                    adx_buy_threshold = np.arange(20, 60, step=20),
                    adx_time_period=np.arange(10, 30, step=15))

                database_interaction.export_hyper_to_db(
                    strategy=strat,
                    hyper=hyper)
                
                #print(f"Execution Time: {time.time() - start_time}")
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

test = Backtest()
test.run_basic_backtest()