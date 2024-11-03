import pandas as pd
import datetime as dt
import numpy as np
import sqlite3 as sql
import inspect
import re
pd.set_option('future.no_silent_downcasting', True)


import pandas as pd

def find_unix(days_ago: int):
    now = dt.datetime.now()
    start = now - dt.timedelta(days=days_ago)
    unix_start_time = int(round(start.timestamp(),0))
    return unix_start_time

def heikin_ashi_transform(dict_df):
    ha_dict = {}

    for symbol, df in dict_df.items():
        ha_df = pd.DataFrame(index=df.index)

        ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

        ha_df.loc[ha_df.index[0], 'open'] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2

        ha_df['high'] = pd.NA
        ha_df['low'] = pd.NA


        for i in range(1, len(df)):
            # Heikin-Ashi Open: midpoint of previous HA_Open and HA_Close
            ha_df.loc[ha_df.index[i], 'open'] = (ha_df.loc[ha_df.index[i-1], 'open'] + ha_df.loc[ha_df.index[i-1], 'close']) / 2

            # Heikin-Ashi High: maximum of the High, HA_Open, and HA_Close of the current bar
            ha_df.loc[ha_df.index[i], 'high'] = max(df['high'].iloc[i], ha_df.loc[ha_df.index[i], 'open'], ha_df.loc[ha_df.index[i], 'close'])

            # Heikin-Ashi Low: minimum of the Low, HA_Open, and HA_Close of the current bar
            ha_df.loc[ha_df.index[i], 'low'] = min(df['low'].iloc[i], ha_df.loc[ha_df.index[i], 'open'], ha_df.loc[ha_df.index[i], 'close'])

        ha_df['volume'] = df['volume']
        ha_df.dropna(inplace=True)


        ha_dict[symbol] = ha_df

    return ha_dict

def to_df(data_dict: dict):
    if not data_dict:
        return pd.DataFrame()  # Return empty DataFrame if data_dict is empty

    key = next(iter(data_dict))  # gets the first key
    df = pd.DataFrame(data_dict[key])  # converts to df

    if key == 'candles':
        if not df.empty:
            df.columns = ['start', 'low', 'high', 'open', 'close', 'volume']
            df['start'] = pd.to_datetime(df['start'].astype(float), unit='s')
            df = df.rename(columns={'start': 'date'})  # renames the start column to date
            df.loc[:, df.columns != 'date'] = df.loc[:, df.columns != 'date'].apply(pd.to_numeric, errors='coerce')
            df = df.ffill()

            # convertts volume to full amount
            move_decimal = lambda val: int(''.join(f"{val:.10f}".rstrip('0').split('.'))) if isinstance(val, float) else val
            df['volume'] = df['volume'].apply(move_decimal)
        else:
            pass
            #print(f"No candle data available.")
    return df
 

