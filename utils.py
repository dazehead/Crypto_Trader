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

def export_hyper_to_db(data, symbol, granularity, strategy_object):
    df = data.to_frame().reset_index()
    df.columns = df.columns.str.replace('cust_', '')
    df = df.rename(columns={df.columns[-1]: 'return_percentage'})
    df['symbol'] = symbol
    #print(df)

    conn = sql.connect('database/hyper.db')
    df.to_sql(f'{strategy_object.__class__.__name__}_{granularity}', conn, if_exists='append', index=False)
    conn.close()

def export_historical_to_df(df, symbol, granularity):
    conn = sql.connect('database/historical_data.db')
    first_date = df.index[0].date()
    last_date = df.index[-1].date()
    table_name = f'{symbol}_{granularity}_{first_date}_TO_{last_date}'.replace('-', '_')

    df.to_sql(table_name, conn, if_exists='append', index=True)
