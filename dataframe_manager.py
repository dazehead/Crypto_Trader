import pandas as pd
import json
import wrapper
import utils
from pickling import to_pickle, from_pickle


class DF_Manager():
    """this only needs to be instansiated during WSClient"""
    def __init__(self,scanner: object, data=None):
        self.scanner = scanner
        self.granularity = scanner.granularity
        self.products_to_trade = scanner.products_to_trade
        if not data:
            self.dict_df = {}
            self.data_for_live_trade()
        else:
            self.dict_df = data
            #self.update(self.df)



    def _to_df(self, dict:dict):
        key = next(iter(dict)) # gets the first key to the dictionary

        if key == 'candles': #not heartbeats only candles
            df = pd.DataFrame(dict[key]) # converts to df
            df['date'] = pd.to_datetime(df['start'].astype(float), unit='s')
            try:
                """this is for WSclient"""
                df = df.drop(columns=['start', 'product_id'])
            except:
                """this is for RESTClient"""
                df = df.drop(column=['start'])
            df.loc[:, df.columns != 'date'] = df.loc[:, df.columns != 'date'].apply(pd.to_numeric, errors='coerce')

            #df = df.ffill()
            df = df.infer_objects(copy=False)#forward fill NANs
        return df

    def process_message(self, message, pickle = False):
        """"""
        msg_data = json.loads(message) # loads data into json format
        if msg_data.get('channel') == 'candles':
            candles_data = msg_data.get('events', [])[0].get('candles', [])

        #print(candles_data)
            if candles_data: # if not an empty list
                if pickle:
                    to_pickle(candles_data)      
                candles_data = {'candles': candles_data} #rename to work with _to_df
                self.new_df = self._to_df(candles_data)
                df = self.dict_df.value()
                df = pd.concat([df, self.new_df], ignore_index = True)
                self.update_df()
                #print(self.df.tail())

        if pickle:
            if msg_data.get('channel') == 'user':
                events = msg_data.get('events', [])
                if events: 
                    order_data = events[0].get('orders', [])
                    if order_data:  
                        order_info = order_data[0]
                list_of_keys = ['order_id',
                                'order_side',
                                'order_type']
                
                for key in list_of_keys:
                    if key in order_info:  
                        pickle_data = order_info[key]
                        to_pickle(pickle_data)

            #print(order_data)
        

    def data_for_live_trade(self, update=False):
        """dataframe needs to be indexed by symbol"""
        for symbol in self.products_to_trade:
            if update:
                timestamps = wrapper.get_unix_times(granularity=self.granularity)
            else:
                timestamps = wrapper.get_unix_times(granularity=self.granularity, days=2)

            dict_df = wrapper.get_basic_candles(client=self.scanner.client,
                            symbols=[symbol],
                            timestamps=timestamps,
                            granularity=self.granularity)
            
            if symbol in self.dict_df:
                last_row = dict_df[symbol].iloc[[-1]]
                self.dict_df[symbol] = pd.concat([self.dict_df[symbol], last_row]).drop_duplicates()
            else: 
                self.dict_df = dict_df

    