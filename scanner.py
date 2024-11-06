import utils
import pandas as pd
import coinbase_wrapper
import time
import sys
class Scanner():
    def __init__(self, client):
        self.client = client
        self.interval = self.client.interval

        self.products = self.client.all_products
        self.products_to_trade = None
        self.df_manager = None
        self.robinhood_crypto = ['BTC', 'ETH', 'DOGE', 'SHIB', 'AVAX', 'BCH', 'LINK', 'UNI', 'LTC', 'XLM', 'ETC', 'AAVE', 'XTZ', 'COMP']
        self.kraken_robinhood_crypto = ['XBTUSD', 'XETHZUSD', 'XDGUSD', 'SHIBUSD', 'AVAXUSD', 'BCHUSD', 'LINKUSD', 'UNIUSD', 'LTCUSD', 'XLMUSD', 'ETCUSD', 'AAVEUSD', 'XTZUSD', 'COMPUSD']


    def assign_attribute(self, df_manager):
        self.df_manager = df_manager

    def populate_manager(self, days_ago=None):
        """currently only using robinhood symbols"""

        start_time = time.time()
        print('Populating DF Manager')
        for i, symbol in enumerate(self.kraken_robinhood_crypto):
            self.df_manager.add_to_manager(self.client.get_historical_data(symbol, days_ago=days_ago))
            utils.progress_bar_with_eta(i, len(self.products), start_time)

    def filter_products(self, filter_type: str=None):
        print('Starting filter')
        self.products_to_trade = self.kraken_robinhood_crypto
        self.df_manager.products_to_trade = self.kraken_robinhood_crypto
        """iterate over all available symbols and only go with volume that is above the average"""
        """iterate overal all availabel symbols and filter by only market cap greater than a value"""



    # def get_product_book(self, product_id):
    #     """gets bids gets asks and time could eventually incorpoate into scanner"""
    #     dict = self.client.get_product_book(product_id=product_id, limit=10)
    #     df = utils.to_df(dict)
    #     pd.set_option('display.max_rows', None)
    #     pd.set_option('display.max_columns', None)
    #     print(df.columns)
    

    # for coinbase not for kraken
    # def get_candles_and_fill_db(self): 
    #     start_time = time.time()
 
    #     self.filter_products(filter_type='SPOT')

    #     timestamps = wrapper.get_unix_times(granularity=self.granularity, days= 365)
    #     for symbol in self.symbols:
    #         dict_df = wrapper.get_candles_for_db(client = self.client,
    #                                 symbols = [symbol],
    #                                 timestamps=timestamps,
    #                                 granularity=self.granularity,
    #                                 fetch_older_data=False)
    #         try:
    #             utils.export_historical_to_db(dict_df=dict_df,
    #                                         granularity=self.granularity)
    #         except KeyError:
    #             print(dict_df.keys())
    #     end_time = time.time()
    #     print(f"Execution time: {(start_time - end_time) / 60} minutes")

