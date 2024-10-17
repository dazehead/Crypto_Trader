import pandas as pd
import datetime as dt
import numpy as np
import sqlite3 as sql
import inspect
import re
pd.set_option('future.no_silent_downcasting', True)

def transform_heikin_ashi(data_dict: dict):
    pass

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
        else:
            pass
            #print(f"No candle data available.")
    return df
 

def export_hyper_to_db(data, strategy_object,granularity):
    symbol = strategy_object.symbol
    df = data.to_frame().reset_index()
    df.columns = df.columns.str.replace('cust_', '')
    df = df.rename(columns={df.columns[-1]: 'return_percentage'})
    df['symbol'] = symbol
    #print(df)

    conn = sql.connect('database/hyper.db')
    df.to_sql(f'{strategy_object.__class__.__name__}_{granularity}', conn, if_exists='append', index=False)
    conn.close()

def export_historical_to_db(dict_df, granularity):
    conn = sql.connect(f'database/{granularity}.db')
    cursor = conn.cursor()
    
    for symbol, df in dict_df.items():
        # Replace hyphens with underscores in symbol
        symbol_pattern = symbol.replace('-', '_')
        # Construct the new table name with the updated date range.
        first_date = df.index[0].date()
        last_date = df.index[-1].date()
        new_table_name = f'{symbol_pattern}_{first_date}_TO_{last_date}'.replace('-', '_')
        
        # Escape underscores in the symbol pattern for the LIKE query
        symbol_pattern_escaped = symbol_pattern.replace('_', r'\_')
        pattern = f'{symbol_pattern_escaped}\\_%'
        
        # Fetch all existing tables matching the pattern
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ? ESCAPE '\\'", (pattern,))
        existing_tables = cursor.fetchall()
        
        # Drop all existing tables that match the pattern
        for existing_table in existing_tables:
            cursor.execute(f'DROP TABLE IF EXISTS \"{existing_table[0]}\"')
            print(f"Dropped table: {existing_table[0]}")
        
        # Write the DataFrame to the new table
        df.drop_duplicates(subset=None, keep='first', inplace=True, ignore_index=False)
        df.to_sql(new_table_name, conn, if_exists='replace', index=True)
        print(f"Created table: {new_table_name}")
    
    conn.commit()
    conn.close()






def get_params_from_strategy(strategy_object):
    symbol = strategy_object.symbol
    backtest_dict = {'symbol': symbol}

    params = inspect.signature(strategy_object.custom_indicator)
    params = list(dict(params.parameters).keys())[1:]

    for param in params:
        value = getattr(strategy_object, param, None)
        backtest_dict[param] = value
    return backtest_dict


def get_metrics_from_backtest(strategy_object, multiple=False, multiple_dict=None):

    symbol = strategy_object.symbol
    portfolio = strategy_object.portfolio
    backtest_dict = {'symbol': symbol}
    if multiple_dict:
        backtest_dict = multiple_dict
    if not multiple:
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
        metric_value = getattr(portfolio, metric)()
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

    if not multiple:
        return backtest_df, value_list, params
    return backtest_df


def export_backtest_to_db(object, granularity, multiple_table_name = None):
    """ object can either be a Strategy Class or a pd.Dataframe"""
    conn = sql.connect('database/backtest.db')

    def _create_table_if_not_exists(table_name, df, conn):
        """ Helper function to create table if it doesn't exist """
        # Check if the table exists
        table_exists_query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
        table_exists = pd.read_sql(table_exists_query, conn)
        
        if table_exists.empty:
            # Create table if it does not exist
            print(f"Table {table_name} doesn't exist. Creating table...")
            columns = df.columns
            dtypes = df.dtypes
            sql_dtypes = []
            for col in columns:
                dtype = dtypes[col]
                if pd.api.types.is_integer_dtype(dtype):
                    sql_dtype = 'INTEGER'
                elif pd.api.types.is_float_dtype(dtype):
                    sql_dtype = 'REAL'
                else:
                    sql_dtype = 'TEXT'
                sql_dtypes.append(f'"{col}" {sql_dtype}')
            create_table_query = f"CREATE TABLE {table_name} ("
            create_table_query += ', '.join(sql_dtypes)
            create_table_query += ");"
            print(create_table_query)
            
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
            print(f"Table {table_name} created successfully.")



    if not isinstance(object, pd.DataFrame):
        strategy_object = object
        backtest_df, value_list, params = get_metrics_from_backtest(strategy_object)
        symbol = backtest_df['symbol'].unique()[0]
        table_name = f"{strategy_object.__class__.__name__}_{granularity}"

        query = f'SELECT * FROM "{table_name}" WHERE symbol = ?'
        delete_query = f'DELETE FROM "{table_name}" WHERE symbol = ?'
        param_query = (symbol,)
        
        for i,param in enumerate(params):
            param_string = f' AND {param} = ?'
            query += param_string
            delete_query += param_string
            param_query += (value_list[i],)
        query += ';'
        delete_query += ';'

        _create_table_if_not_exists(table_name, backtest_df, conn)

        # print(f"param_query: {param_query}")
        # print(f"param_string: {param_string}")
        # print(f"query: {query}")
        # print(f"delete_query: {delete_query}")

    else:
        backtest_df = object
        table_name = f"{multiple_table_name}_{granularity}"

        start_col = backtest_df.columns.get_loc('symbol')
        end_col = backtest_df.columns.get_loc('annual_returns')
        subset_df = backtest_df.iloc[:, start_col:end_col]

        query = f'SELECT * FROM "{table_name}" WHERE symbol = ?'
        delete_query = f'DELETE FROM "{table_name}" WHERE symbol = ?'

        param_values = subset_df.iloc[0].values
        param_values_converted = [
            int(x) if isinstance(x, np.integer)
            else float(x) if isinstance(x, np.floating)
            else x
            for x in param_values
        ]

        param_query = tuple(param_values_converted)
        columns = subset_df.columns.drop('symbol')
        param_string = ' AND '.join([f'"{col}" = ?' for col in columns])
        query += f" AND {param_string};"
        delete_query += f" AND {param_string};"

        _create_table_if_not_exists(table_name, backtest_df, conn)

        # print(f"param_query: {param_query}")
        # print(f"param_string: {param_string}")
        # print(f"query: {query}")
        # print(f"delete_query: {delete_query}")


    existing_row = pd.read_sql(query, conn, params=param_query)



    if not existing_row.empty:
        cursor = conn.cursor()
        cursor.execute(delete_query, param_query)
        conn.commit()

        backtest_df.to_sql(table_name, conn, if_exists='append', index=False)

    else:
        backtest_df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.close()
    pass
