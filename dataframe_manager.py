import pandas as pd
import json

class DF_Manager():
    """this only needs to be instansiated during WSClient"""
    def __init__(self, df=None):
        self.first_candle = True
        self.df = pd.DataFrame()
        if df:
            self.df = df


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

    def process_message(self, message):
        msg_data = json.loads(message) # loads data into json format
        candles_data = msg_data.get('events', [])[0].get('candles', []) # retrives data if there is some if not an empty list

        if candles_data: # if not an empty list
            candles_data = {'candles': candles_data} #rename to work with _to_df
            self.new_df = self._to_df(candles_data)
            self.df = pd.concat([self.df, self.new_df], ignore_index = True)
            print(self.df.tail())

