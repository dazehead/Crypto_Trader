import utils
import pandas as pd

class Scanner():
    def __init__(self, rest_client, granularity):
        self.rest_client = rest_client
        self.graularity = granularity

        self.products = self.get_products()

        self.products_to_trade = self.filter_products()

    def filter_products(self):
        filter_list = []
        """
        this is where we define what we want our filter to be such as 
        for each product in self.products
            if market trades are > 1000000
            or if change percentage is > 20%
            then append that product to self.filter_products
        """
        return filter_list




    """all the function below came from the rest_testbed while exploring calls on the api"""
    def get_product_book(self, product_id):
        """gets bids gets asks and time could eventually incorpoate into scanner"""
        dict = self.rest_client.get_product_book(product_id=product_id, limit=10)
        df = utils.to_df(dict)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        print(df.columns)


    def get_products(self, client, only_price = False):
        """lots of data in df to use in scanner such as volume, and change percentage"""

        pd.set_option('display.float_format', lambda x: '%.6f' % x)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        dict = client.get_products(get_all_products=True)
        df = utils.to_df(dict)
        if only_price:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df[['product_id', 'price']].sort_values(by='price', ascending=False)
        return df


    def get_best_bid_ask(self, product_id):
        """gets the best bid and ask"""

        dict = self.rest_client.get_best_bid_ask(product_ids=[product_id])
        df = utils.to_df(dict)
        print(df.head())


    def get_market_trades(self, product_id):
        """get the last market trades that have occured"""

        timestamps = utils.get_unix_times(granularity=self.granularity)
        dict = self.rest_client.get_market_trades(product_id=product_id, limit = 10, start=timestamps[0][1], end=timestamps[0][0])
        df = utils.to_df(dict)
        print(df.head())
