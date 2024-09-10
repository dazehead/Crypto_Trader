import pandas as pd
import datetime as dt
pd.set_option('future.no_silent_downcasting', True)

def _to_df(candles:dict):
    df = pd.DataFrame(candles['candles']) # converts to df
    df['start'] = pd.to_datetime(df['start'].astype(float), unit='s')
    df = df.rename(columns={'start': 'date'}) # renames the start colum to date
    df.loc[:, df.columns != 'date'] = df.loc[:, df.columns != 'date'].apply(pd.to_numeric, errors='coerce')
    df = df.ffill()

    return df

