import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import core.utils as utils
import datetime as dt
import numpy as np
import core.database_interaction as database_interaction
import time
import gc
import gc
import io
import base64
from coinbase.rest import RESTClient
from core.strategies.strategy import Strategy
from core.strategies.single.efratio import EFratio
from core.strategies.single.vwap import Vwap
from core.strategies.single.rsi import RSI
from core.strategies.single.atr import ATR
from core.strategies.single.macd import MACD
from core.strategies.single.kama import Kama
from core.strategies.single.adx import ADX
from core.strategies.single.bollinger import BollingerBands
from core.strategies.double.rsi_adx import RSI_ADX
from core.strategies.combined_strategy import Combined_Strategy
from core.strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
from core.strategies.gpu_optimized.rsi_adx_np import RSI_ADX_NP
from core.strategies.gpu_optimized.rsi_bollinger_np import BollingerBands_RSI
from core.risk import Risk_Handler
from core.log import LinkedList
from core.hyper import Hyper
import plotly
from io import BytesIO
from PIL import Image
#pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)
import logging
# logging.basicConfig(level=logging.DEBUG)
logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("numpy").setLevel(logging.WARNING)

# Set your own logging level if needed
logging.basicConfig(level=logging.INFO) 




class Backtest():
    def __init__(self):
        self.symbols = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SHIB-USD', 'AVAX-USD', 'BCH-USD', 'LINK-USD', 'UNI-USD', 'LTC-USD', 'XLM-USD', 'ETC-USD', 'AAVE-USD', 'XTZ-USD', 'COMP-USD']
        self.granularites = ['ONE_MINUTE','FIVE_MINUTE','FIFTEEN_MINUTE','THIRTY_MINUTE','ONE_HOUR','TWO_HOUR','SIX_HOUR','ONE_DAY']
        self.product = ['XTZ-USD']
        self.granularity = 'ONE_MINUTE'
        

    def run_multiple_strategy(self, symbol: str, granularity: str, num_days: int, sizing:bool, graph_callback =None, strategies:list = []):
        logbook = LinkedList()
        dict_df = database_interaction.get_historical_from_db(granularity=granularity, symbols=symbol, num_days=num_days)
        risk = Risk_Handler()

        #for sym, df in df_dict.items():
            #current_dict_df = {sym:df}

        combined_strat = Combined_Strategy(dict_df, risk, sizing,*strategies)
        combined_strat.generate_combined_signals()
        combined_strat.graph(graph_callback)
        combined_strat.generate_backtest()
        print(combined_strat.portfolio.stats(silence_warnings=True))

        logbook.insert_beginning(combined_strat)
        
        logbook.export_multiple_pf_to_db(is_combined=True)



    def run_basic_backtest(self, symbol, granularity, strategy_obj, num_days, sizing, best_params=True, graph_callback=None):
        print(symbol, granularity, strategy_obj, num_days, sizing, best_params, graph_callback)
        print("Getting historical data...")
        dict_df = database_interaction.get_historical_from_db(
            granularity=granularity,
            symbols=symbol,
            num_days=num_days
        )
        if not dict_df:
            raise ValueError("No historical data found for the given parameters.")
        print("Fetched historical data:", dict_df)

        stats = {}
        graph_base64 = None

        logging.info(f"Running backtest for {len(dict_df)} symbols")

        for key, value in dict_df.items():
            try:
                current_dict = {key: value}
                risk = Risk_Handler()
                strat = strategy_obj(
                    dict_df=current_dict,
                    risk_object=risk,
                    with_sizing=sizing,
                )

                
                if best_params:
                    print("getting best parameters ...")
                    logging.info(f"Getting best parameters for {strat.__class__.__name__}")
                    params = database_interaction.get_best_params(strat, minimum_trades=4)
                    logging.info(f"Best params: {params}")
                    strat.custom_indicator(None, *params)
                else:
                    try:
                        print("running custom indicator ...")
                        logging.info(f"Running custom indicator for {strat.__class__.__name__}")
                        strat.custom_indicator()
                    except Exception as e:
                        logging.error(f"Error running custom indicator: {e}")
                        print(f"Error running custom indicator: {e}")
                        continue
                try:
                    print("graphing ...")
                    logging.info(f"Graphing for {strat.__class__.__name__}")
                    strat.graph()
                except Exception as e:
                    logging.error(f"Error graphing: {e}")
                    print(f"Error graphing: {e}")    

                try:
                    logging.info(f"Generating backtest for {strat.__class__.__name__}") 
                    print("generating backtest...")
                    strat.generate_backtest()
                    logging.info(f"Portfolio after backtest: {strat.portfolio}")
                    pf = strat.portfolio
                    print("assigning portfolio")
                    stats = pf.stats().to_dict()
                    print("generating stats ...")
                    print(f"stats: ")
                    print(stats)
                except Exception as e:
                    print(f"Error in backtest iteration for {key}: {e}")

                if graph_callback:
                    try:
                        fig = pf.plot(subplots=['orders'])
                        graph_base64 = graph_callback(fig)
                    except Exception as e:
                        logging.error(f"Graph generation failed: {e}")
                        print(f"Graph generation failed: {e}")
                        graph_base64 = ""

            except Exception as e:
                print(f"Error in backtest iteration for {key}: {e}")

        if not stats:
            stats = {"error": "No stats generated"}
        if not graph_base64:
            logging.info("No graph generated")
            graph_base64 = ""

        return stats, graph_base64


            # fig = pf.plot(subplots = [
            # 'orders',
            # 'trade_pnl',
            # 'cum_returns',
            # 'drawdowns',
            # 'underwater',
            # 'gross_exposure'])
            # fig.update_layout(
            #     title={
            #         'text': f"{strat.__class__.__name__} for {strat.symbol} on {strat.granularity} timeframe",  # Replace with your desired title
            #         'x': 0.5,  # Centers the title
            #         'xanchor': 'center',
            #         'yanchor': 'top'
            #     },
            #     margin={
            #         't': 100  # Adjust the top margin to create space for the title
            #     }
            # )
                

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
                                                                num_days=25)
            print(f'...Running hyper on {len(self.symbols)} symbols')

            #dict_df = utils.heikin_ashi_transform(dict_df)

            start_time = time.time()
            for i,items in enumerate(dict_df.items()):
                key, value = items
                current_dict = {key:value}
                
                strat = BollingerBands_RSI(current_dict, risk_object=risk, with_sizing=True)

                hyper = Hyper(
                    strategy_object=strat,
                    close=strat.close,
                    bb_period=np.arange(10, 30, step=5),  # Matches bb_period range
                    bb_dev=np.arange(1, 3, step=0.5),    # Matches bb_dev range
                    rsi_window=np.arange(10, 20, step=2),# Matches rsi_window range
                    rsi_buy=np.arange(20, 40, step=5),   # Matches rsi_buy range
                    rsi_sell=np.arange(60, 80, step=5)   # Matches rsi_sell range
                )


                database_interaction.export_hyper_to_db(
                    strategy=strat,
                    hyper=hyper)
                
                print(f"Execution Time: {time.time() - start_time}")
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
    def run_optimization_tests(self, strategy_class, param_ranges, train_test_split=0.7):
        """
        Run optimization tests with walk-forward analysis for multiple symbols and granularities.

        Args:
            strategy_class: The strategy class to test (e.g., RSI_ADX_GPU).
            param_ranges: Dictionary of hyperparameter ranges for optimization.
            train_test_split: Proportion of data to use for training (default: 70% train, 30% test).
        """
        results = []
        risk = Risk_Handler()

        for granularity in self.granularites:
            num_days = {
                'ONE_MINUTE': 1095,
                'FIVE_MINUTE': 1095,
                'FIFTEEN_MINUTE': 1095,
                'THIRTY_MINUTE': 1095,
                'ONE_HOUR': 1095,
                'TWO_HOUR': 1095,
                'SIX_HOUR': 1095,
                'ONE_DAY': 1095,
            }.get(granularity, 1095)

            logging.info(f"Processing granularity: {granularity}, num_days: {num_days}")

            for symbol in self.symbols:
                try:
                    # Fetch historical data
                    logging.info(f"Fetching historical data for {symbol} at {granularity}")
                    dict_df = database_interaction.get_historical_from_db(
                        granularity=granularity,
                        symbols=symbol,
                        num_days=num_days
                    )
                    if not dict_df or symbol not in dict_df:
                        logging.warning(f"No data available for {symbol} at {granularity}")
                        continue

                    data = dict_df[symbol]
                    logging.info(f"Fetched data for {symbol}: {data.shape[0]} rows")

                    total_len = len(data)
                    train_len = int(total_len * train_test_split)

                    if train_len < 1 or total_len - train_len < 1:
                        logging.warning(f"Insufficient data for training/testing split for {symbol} at {granularity}")
                        continue

                    # Walk-forward analysis
                    for start_idx in range(0, total_len - train_len, train_len // 2):
                        try:
                            logging.info(f"Processing window: start_idx={start_idx}, train_len={train_len}")
                            train_data = data.iloc[start_idx: start_idx + train_len]
                            test_data = data.iloc[start_idx + train_len: start_idx + 2 * train_len]

                            if len(test_data) < 1:
                                logging.warning(f"Skipping incomplete test window for {symbol} at {granularity}")
                                break

                            # Optimize on train_data
                            strat_train = strategy_class(
                                dict_df={symbol: train_data},
                                risk_object=risk,
                                with_sizing=True
                            )
                            hyper = Hyper(
                                strategy_object=strat_train,
                                close=strat_train.close,
                                **param_ranges
                            )

                            database_interaction.export_hyper_to_db(
                                strategy=strat_train,
                                hyper=hyper
                            )

                            best_params = database_interaction.get_best_params(strat_train)
                            logging.info(f"Best params for {symbol} at {granularity}: {best_params}")

                            # Test on test_data
                            strat_test = strategy_class(
                                dict_df={symbol: test_data},
                                risk_object=risk,
                                with_sizing=True
                            )
                            strat_test.custom_indicator(None, *best_params)
                            strat_test.generate_backtest()
                            stats = strat_test.portfolio.stats(silence_warnings=True).to_dict()
                            stats = strat_test.portfolio.stats(silence_warnings=True).to_dict()

                            # Filter stats to only include the specified metrics
                            filtered_stats = {
                                key: stats[key]
                                for key in [
                                    'Total Return [%]',
                                    'Total Trades',
                                    'Win Rate [%]',
                                    'Best Trade [%]',
                                    'Worst Trade [%]',
                                    'Avg Winning Trade [%]',
                                    'Avg Losing Trade [%]',
                                ]
                                if key in stats
                            }

                            # Add additional metadata fields
                            filtered_stats.update({
                                "symbol": symbol,
                                "granularity": granularity,
                                "start_idx": start_idx,
                                "end_idx": start_idx + train_len,
                            })

                            # Add to results
                            results.append(filtered_stats)


                            del strat_train, strat_test, hyper
                            gc.collect()
                        except Exception as e:
                            logging.error(f"Error during walk-forward window processing: {e}", exc_info=True)
                except Exception as e:
                    logging.error(f"Error processing {symbol} at {granularity}: {e}", exc_info=True)

        # Convert results to DataFrame for easier analysis
        results_df = pd.DataFrame(results)


        if results_df.empty:
            logging.warning("Results DataFrame is empty. Nothing to export.")
            return

        logging.info(f"Results DataFrame:\n{results_df.head()}")

        try:
            database_interaction.export_optimization_results(results_df)
            logging.info("Optimization results exported successfully.")
        except Exception as e:
            logging.error(f"Error exporting optimization results: {e}", exc_info=True)

        return results_df

