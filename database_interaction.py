import pandas as pd
import utils
import sqlite3 as sql
import inspect
import numpy as np
import sys
import time
import gc


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

        # Get the total number of rows in the table
        count_query = f'SELECT COUNT(*) FROM "{table}"'
        total_rows = pd.read_sql_query(count_query, conn).iloc[0, 0]

        # Initialize the variable to store all data
        data = pd.DataFrame()

        # Fetch data in chunks (paging)
        for offset in range(0, total_rows, page_size):
            paged_query = f'SELECT * FROM "{table}" LIMIT {page_size} OFFSET {offset}'
            chunk = pd.read_sql_query(paged_query, conn)
            
            # Convert 'date' column to datetime and set as index
            chunk['date'] = pd.to_datetime(chunk['date'], errors='coerce')
            chunk.set_index('date', inplace=True)

            # If num_days is provided, filter the data based on the most recent date
            if num_days is not None:
                last_date = chunk.index.max()  # Find the most recent date in the dataset
                start_date = last_date - pd.Timedelta(days=num_days)
                chunk = chunk.loc[chunk.index >= start_date]

            # Append the chunk to the data DataFrame
            data = data._append(chunk)

        # Store the data in the dictionary
        tables_data[clean_table_name] = data

    conn.close()
    return tables_data

def get_hyper_from_db(strategy_object):
    conn = sql.connect(f'database/hyper.db')
    table = f"{strategy_object.__class__.__name__}_{strategy_object.granularity}"
    params = inspect.signature(strategy_object.custom_indicator)
    params = list(dict(params.parameters).keys())[1:]
    print(params)
    parameters = ', '.join(params)
    query = f'SELECT {parameters},MAX("Total Return [%]") FROM {table} WHERE symbol="{strategy_object.symbol}"'
    result = pd.read_sql_query(query, conn)
    print(result)
    conn.close()
    #return tables_data


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
            'Avg Losing Trade [%]',
            'Sharpe Ratio',
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

    table_name = f"{strategy.__class__.__name__}_{granularity}"

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

        utils.export_historical_to_db(resampled_dict_df, granularity=key)

    print("Resampling completed.")

