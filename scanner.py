import utils
import pandas as pd
import wrapper
import time

class Scanner():
    def __init__(self, rest_client, granularity):
        self.client = rest_client
        self.granularity = granularity

        self.products = self.get_products(filter_type='SPOT')
        self.symbols = None
        self.products_to_trade = ['BTC-USD']#self.filter_products()



    def filter_products(self, filter_type: str=None):
        acceptable_values = ['FUTURE','SPOT']
        if filter_type:
            if filter_type not in acceptable_values:
                print(f'filter_type needs to be one of these values {acceptable_values}')
                return
            self.products = self.products[self.products['product_type'] == filter_type]
            self.symbols = list(self.products['product_id'])
        return self.products


    """all the function below came from the rest_testbed while exploring calls on the api"""
    def get_product_book(self, product_id):
        """gets bids gets asks and time could eventually incorpoate into scanner"""
        dict = self.client.get_product_book(product_id=product_id, limit=10)
        df = utils.to_df(dict)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        print(df.columns)
    

    def get_products(self, only_price = False, filter_type: str=None):
        """lots of data in df to use in scanner such as volume, and change percentage"""

        pd.set_option('display.float_format', lambda x: '%.6f' % x)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        dict = self.client.get_products(get_all_products=True)
        df = utils.to_df(dict)
        if only_price:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df[['product_id', 'price']].sort_values(by='price', ascending=False)
        return df

    def get_candles_and_fill_db(self):
        start_time = time.time()
 
        self.filter_products(filter_type='SPOT')

        timestamps = wrapper.get_unix_times(granularity=self.granularity, days= 365)
        for symbol in self.symbols:
            dict_df = wrapper.get_candles_for_db(client = self.client,
                                    symbols = [symbol],
                                    timestamps=timestamps,
                                    granularity=self.granularity,
                                    fetch_older_data=False)
            try:
                utils.export_historical_to_db(dict_df=dict_df,
                                            granularity=self.granularity)
            except KeyError:
                print(dict_df.keys())
        end_time = time.time()
        print(f"Execution time: {(start_time - end_time) / 60} minutes")

    def get_best_bid_ask(self, product_id):
        """gets the best bid and ask"""

        dict = self.client.get_best_bid_ask(product_ids=[product_id])
        df = utils.to_df(dict)
        print(df.head())


    def get_market_trades(self, product_id):
        """get the last market trades that have occured"""

        timestamps = utils.get_unix_times(granularity=self.granularity)
        dict = self.client.get_market_trades(product_id=product_id, limit = 10, start=timestamps[0][1], end=timestamps[0][0])
        df = utils.to_df(dict)
        print(df.head())
