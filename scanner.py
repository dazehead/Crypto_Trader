import utils
import pandas as pd
import wrapper
import time

class Scanner():
    def __init__(self, client):
        self.client = client
        self.interval = self.client.interval

        self.products = self.client.all_products
        self.products_to_trade = None



    def filter_products(self, filter_type: str=None):
        #print(self.products)
        print('This is where we filter the products')
        self.products_to_trade = ['XBTUSD']


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

