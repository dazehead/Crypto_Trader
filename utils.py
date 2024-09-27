import pandas as pd
import datetime as dt
import numpy as np
import sqlite3 as sql
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
 
def get_historical_from_db():
    conn = sql.connect('database/historical_data.db')
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    tables_data = {}
    for table in tables['name']:
        data = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        data.set_index('date', inplace=True)
        tables_data[table] = data
    conn.close()

    return tables_data


