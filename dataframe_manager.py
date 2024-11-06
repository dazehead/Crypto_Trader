import pandas as pd
import json
import coinbase_wrapper
import utils
from pickling import to_pickle, from_pickle


class DF_Manager():
    """this only needs to be instansiated during WSClient"""
    def __init__(self,scanner: object, data=None):
        self.scanner = scanner
        self.client = self.scanner.client
        self.interval = self.scanner.interval
        self.products_to_trade = scanner.products_to_trade
        if not data:
            self.dict_df = {}
            #self.data_for_live_trade()
        else:
            self.dict_df = data
            #self.update(self.df)

    def add_to_manager(self, data):
        if not self.dict_df:
            self.dict_df = data
        else:
            for k, v in data.items():
                self.dict_df[k] = v


    def data_for_live_trade(self, update=False):
        """dataframe needs to be indexed by symbol"""
        for symbol in self.products_to_trade:
            # Get the historical data
            days_ago = 1 if update else 2
            historical_data = self.client.get_historical_data(symbol, days_ago=days_ago)
            updated_symbol = list(historical_data.keys())[0]
            
            # If updating, add only the last row if symbol exists
            if update:
                last_row = historical_data[updated_symbol].iloc[[-1]]
                self.dict_df[updated_symbol] = pd.concat([self.dict_df[updated_symbol], last_row]).drop_duplicates()
                print(f"Updated {updated_symbol}")
            else:
                self.dict_df[updated_symbol] = historical_data[updated_symbol]

    
    # def _to_df(self, dict:dict):
    #     key = next(iter(dict)) # gets the first key to the dictionary

    #     if key == 'candles': #not heartbeats only candles
    #         df = pd.DataFrame(dict[key]) # converts to df
    #         df['date'] = pd.to_datetime(df['start'].astype(float), unit='s')
    #         try:
    #             """this is for WSclient"""
    #             df = df.drop(columns=['start', 'product_id'])
    #         except:
    #             """this is for RESTClient"""
    #             df = df.drop(column=['start'])
    #         df.loc[:, df.columns != 'date'] = df.loc[:, df.columns != 'date'].apply(pd.to_numeric, errors='coerce')

    #         #df = df.ffill()
    #         df = df.infer_objects(copy=False)#forward fill NANs
    #     return df

    # def process_message(self, message, pickle = False):
    #     """"""
    #     msg_data = json.loads(message) # loads data into json format
    #     if msg_data.get('channel') == 'candles':
    #         candles_data = msg_data.get('events', [])[0].get('candles', [])

    #     #print(candles_data)
    #         if candles_data: # if not an empty list
    #             if pickle:
    #                 to_pickle(candles_data)      
    #             candles_data = {'candles': candles_data} #rename to work with _to_df
    #             self.new_df = self._to_df(candles_data)
    #             df = self.dict_df.value()
    #             df = pd.concat([df, self.new_df], ignore_index = True)
    #             self.update_df()
    #             #print(self.df.tail())

    #     if pickle:
    #         if msg_data.get('channel') == 'user':
    #             events = msg_data.get('events', [])
    #             if events: 
    #                 order_data = events[0].get('orders', [])
    #                 if order_data:  
    #                     order_info = order_data[0]
    #             list_of_keys = ['order_id',
    #                             'order_side',
    #                             'order_type']
                
    #             for key in list_of_keys:
    #                 if key in order_info:  
    #                     pickle_data = order_info[key]
    #                     to_pickle(pickle_data)

    #         #print(order_data)
        


    