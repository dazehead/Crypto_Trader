import pandas as pd
import datetime as dt
pd.set_option('future.no_silent_downcasting', True)

def to_df(dict:dict):
    """some dicts may have more than 1 as of right now the second is only the length"""
    print(f"Length of dictionary : {len(dict.keys())}")
    for i, key in enumerate(dict.keys()):
        if i == 1:
            break
        df = pd.DataFrame(dict[key]) # converts to df
        if key == 'candles':
            df['start'] = pd.to_datetime(df['start'].astype(float), unit='s')
            df = df.rename(columns={'start': 'date'}) # renames the start colum to date
            df.loc[:, df.columns != 'date'] = df.loc[:, df.columns != 'date'].apply(pd.to_numeric, errors='coerce')
            df = df.ffill()
    return df
 
    
