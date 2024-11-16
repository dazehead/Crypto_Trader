import pandas as pd
import utils
import sqlite3 as sql
import inspect
import numpy as np
import sys
import time
import gc


def convert_symbols(strategy_object:object):
    coinbase_crypto = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SHIB-USD', 'AVAX-USD', 'BCH-USD', 'LINK-USD', 'UNI-USD', 'LTC-USD', 'XLM-USD', 'ETC-USD', 'AAVE-USD', 'XTZ-USD', 'COMP-USD']
    robinhood_crypto = ['BTC', 'ETH', 'DOGE', 'SHIB', 'AVAX', 'BCH', 'LINK', 'UNI', 'LTC', 'XLM', 'ETC', 'AAVE', 'XTZ', 'COMP']
    kraken_crypto = ['XXBTZUSD', 'XETHZUSD', 'XDGUSD', 'SHIBUSD', 'AVAXUSD', 'BCHUSD', 'LINKUSD', 'UNIUSD', 'XLTCZUSD', 'XXLMZUSD', 'XETCZUSD', 'AAVEUSD', 'XTZUSD', 'COMPUSD']

    database_list = coinbase_crypto
    symbol_list = kraken_crypto
    current_symbol =  strategy_object.symbol
    symbol_index = kraken_crypto.index(current_symbol)
    return coinbase_crypto[symbol_index]




def get_historical_from_db(granularity, symbols: list = [], num_days: int = None):
    conn = sql.connect(f'database/{granularity}.db')
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    tables_data = {}
    
    for table in tables['name']:
        clean_table_name = '-'.join(table.split('_')[:2])

        # If symbols are provided, skip tables that are not in the symbol list
        if symbols and clean_table_name not in symbols:
            continue

        # Retrieve data from the table
        data = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        data.set_index('date', inplace=True)

        # If num_days is provided, filter the data based on the most recent date
        if num_days is not None:
            last_date = data.index.max()  # Find the most recent date in the dataset
            start_date = last_date - pd.Timedelta(days=num_days)
            data = data.loc[data.index >= start_date]

        # Store the data in the dictionary
        tables_data[clean_table_name] = data
    
    conn.close()
    return tables_data


def get_best_params(strategy_object):
    conn = sql.connect(f'database/hyper.db')
    table = f"{strategy_object.__class__.__name__}_{strategy_object.granularity}"
    params = inspect.signature(strategy_object.custom_indicator)
    params = list(dict(params.parameters).keys())[1:]
    parameters = ', '.join(params)

    # we have already sent it the correct symbols that it did not get from client
    if strategy_object.risk_object.client is not None:
        symbol = convert_symbols(strategy_object = strategy_object)
    else:
        symbol = strategy_object.symbol

    query = f'SELECT {parameters},MAX("Total Return [%]") FROM {table} WHERE symbol="{symbol}"'
    result = pd.read_sql_query(query, conn)

    list_results = []

    for param in result:
        list_results.append(result[param][0])
    list_results = list_results[:-1]  

    conn.close()
    return list_results


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
        return

def export_hyper_to_db(strategy: object, hyper: object):
    stats_to_export = [
            'Total Return [%]',
            'Total Trades',
            'Win Rate [%]',
            'Best Trade [%]',
            'Worst Trade [%]',
            'Avg Winning Trade [%]',
            'Avg Losing Trade [%]'
        ]
    
    data = hyper.pf.stats()

    conn = sql.connect('database/hyper.db')

    symbol = strategy.symbol
    granularity = strategy.granularity
    params = inspect.signature(strategy.custom_indicator)
    params = list(dict(params.parameters).keys())[1:]
    combined_df = pd.DataFrame()

    for i in range(len(data)):
        stats = data.iloc[i]
        backtest_dict = {'symbol': symbol}
        for j,param in enumerate(params):
            backtest_dict[param] = stats.name[j]

        for key, value in stats.items():
            if key in stats_to_export:
                backtest_dict[key] = value

        combined_df = pd.concat([combined_df,pd.DataFrame([backtest_dict])])

    class_name = strategy.__class__.__name__
    if class_name.split('_')[-1] == 'GPU':
        class_name = '_'.join(class_name.split('_')[:-1])
        
    table_name = f"{class_name}_{granularity}"

    _create_table_if_not_exists(table_name, combined_df, conn=conn) 

    query = f'SELECT * FROM "{table_name}" WHERE symbol = "{symbol}";'
    delete_query = f'DELETE FROM "{table_name}" WHERE symbol = "{symbol}";'

    existing_data = pd.read_sql(query, conn)
    
    if not existing_data.empty:
        cursor = conn.cursor()
        cursor.execute(delete_query)
        conn.commit()

        combined_df.to_sql(table_name, conn, if_exists='append', index=False)

    else:
        combined_df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()
    return


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
            #print(f"Dropped table: {existing_table[0]}")
        
        # Write the DataFrame to the new table
        df.drop_duplicates(subset=None, keep='first', inplace=True, ignore_index=False)
        df.to_sql(new_table_name, conn, if_exists='replace', index=True)
        #print(f"\nCreated table: {new_table_name}")
    
    conn.commit()
    conn.close()


def resample_dataframe_from_db(granularity='ONE_MINUTE'):
    """
    Resamples data from the database for different timeframes based on the granularity.
    """
    times_to_resample = {
        'FIVE_MINUTE': '5min',
        'FIFTEEN_MINUTE': '15min',
        'THIRTY_MINUTE': '30min',
        'ONE_HOUR': '1h',
        'TWO_HOUR': '2h',
        'SIX_HOUR': '6h',
        'ONE_DAY': '1D'
    }


    dict_df = get_historical_from_db(granularity=granularity)

    resampled_dict_df = {}

    for key, value in times_to_resample.items():
        for symbol, df in dict_df.items():
            df = df.sort_index()

            df_resampled = df.resample(value).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })

            df_resampled.dropna(inplace=True)

            print(f"Resampled {symbol} to {key}")
            resampled_dict_df[symbol] = df_resampled

        export_historical_to_db(resampled_dict_df, granularity=key)

    print("Resampling completed.")






############################################### for backtest;however, will need to re-do...maybe ################################################################


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
    

    stats_to_export = [
        'Total Return [%]',
        'Total Trades',
        'Win Rate [%]',
        'Best Trade [%]',
        'Worst Trade [%]',
        'Avg Winning Trade [%]',
        'Avg Losing Trade [%]'
    ]

    for key, value in portfolio.stats().items():
        if key in stats_to_export:
            backtest_dict[key] = value

    backtest_df = pd.DataFrame([backtest_dict])

    if not multiple:
        return backtest_df, value_list, params
    return backtest_df




def export_backtest_to_db(object, multiple_table_name=None):
    """ object can either be a Strategy Class or a pd.DataFrame """
    conn = sql.connect('database/backtest.db')

    if not isinstance(object, pd.DataFrame):
        # Handle Strategy object
        strategy_object = object
        granularity = strategy_object.granularity
        backtest_df, value_list, params = get_metrics_from_backtest(strategy_object)
        symbol = backtest_df['symbol'].unique()[0]
        table_name = f"{strategy_object.__class__.__name__}_{granularity}"

        # Ensure the table exists
        _create_table_if_not_exists(table_name, backtest_df, conn)

        # Prepare the DELETE query
        delete_query = f'DELETE FROM "{table_name}" WHERE symbol = ?'
        param_query = (symbol,)

    else:
        # Handle DataFrame directly
        backtest_df = object
        granularity = "default_granularity"  # Fallback granularity if not provided
        table_name = f"{multiple_table_name}_{granularity}"

        # Ensure the table exists
        _create_table_if_not_exists(table_name, backtest_df, conn)

        # Prepare the DELETE query
        symbol = backtest_df['symbol'].unique()[0]
        delete_query = f'DELETE FROM "{table_name}" WHERE symbol = ?'
        param_query = (symbol,)

    # Step 1: Delete existing rows with the same symbol
    cursor = conn.cursor()
    cursor.execute(delete_query, param_query)
    conn.commit()

    # Step 2: Insert the updated data
    backtest_df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.close()
    return