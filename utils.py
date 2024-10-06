import pandas as pd
import datetime as dt
import numpy as np
import sqlite3 as sql
import inspect
import re
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
 
def get_historical_from_db(granularity):
    conn = sql.connect(f'database/{granularity}.db')
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    tables_data = {}

    for table in tables['name']:
        data = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
        data.set_index('date', inplace=True)
        clean_table_name = '-'.join(table.split('_')[:2])
        tables_data[clean_table_name] = data
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

def export_historical_to_db(df, symbol, granularity):
    conn = sql.connect(f'database/{granularity}.db')
    first_date = df.index[0].date()
    last_date = df.index[-1].date()
    table_name = f'{symbol}_{first_date}_TO_{last_date}'.replace('-', '_')

    df.to_sql(table_name, conn, if_exists='append', index=True)


def export_backtest_to_db(strategy_object, symbol, granularity):
    symbol = strategy_object.symbol
    portfolio = strategy_object.portfolio
    backtest_dict = {'symbol': symbol}

    params = inspect.signature(strategy_object.custom_indicator)
    params = list(dict(params.parameters).keys())[1:]
    value_list = []

    for param in params:
        value = getattr(strategy_object, param, None)
        backtest_dict[param] = value
        value_list.append(value)
    
    functions_to_export = [
        'annual_returns',
        'downside_risk',
        'value_at_risk'
    ]

    for metric in functions_to_export:
        metric_value = getattr(strategy_object.portfolio, metric)()

        if isinstance(metric_value, (pd.Series, pd.DataFrame)):
             metric_value = metric_value.iloc[0]
        backtest_dict[metric] = metric_value
    
    stats_to_export = [
        'Total Return [%]',
        'Total Trades',
        'Win Rate [%]',
        'Best Trade [%]',
        'Worst Trade [%]',
        'Avg Winning Trade [%]',
        'Avg Losing Trade [%]',
        'Sharpe Ratio',
    ]

    for key, value in portfolio.stats().items():
        if key in stats_to_export:
            backtest_dict[key] = value

    backtest_df = pd.DataFrame([backtest_dict])

    table_name = f"{strategy_object.__class__.__name__}_{granularity}"
    conn= sql.connect('database/backtest.db')

    query = f"SELECT * FROM {table_name} WHERE symbol = ? "
    delete_query = f"DELETE FROM {table_name} WHERE symbol = ? "
    param_query = (symbol,)
    
    for i,param in enumerate(params):
        param_string = f"AND {param} = ? "
        query += param_string
        delete_query += param_string
        param_query += (value_list[i],)
    query += ';'
    delete_query += ';'

    existing_row = pd.read_sql(query.replace('-','_'), conn, params=param_query)

    if not existing_row.empty:
        cursor = conn.cursor()
        cursor.execute(delete_query, param_query)
        conn.commit()

        backtest_df.to_sql(table_name, conn, if_exists='append', index=False)

    else:
        backtest_df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.close()

def export_mulitple_to_db(strat, granularity):
    pass


