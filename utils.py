import pandas as pd
import datetime as dt
import numpy as np
pd.set_option('future.no_silent_downcasting', True)

def to_df(dict:dict):
    key = next(iter(dict)) # gets the first key
    df = pd.DataFrame(dict[key]) # converts to df
    if key == 'candles':
        df['start'] = pd.to_datetime(df['start'].astype(float), unit='s')
        df = df.rename(columns={'start': 'date'}) # renames the start colum to date
        df.loc[:, df.columns != 'date'] = df.loc[:, df.columns != 'date'].apply(pd.to_numeric, errors='coerce')
        df = df.ffill()
    return df
 