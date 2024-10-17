import pandas as pd
import utils
import sqlite3 as sql

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


    dict_df = utils.get_historical_from_db(granularity=granularity)

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

resample_dataframe_from_db()

def get_historical_from_db(granularity):
    conn = sql.connect(f'database/{granularity}.db')
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    tables_data = {}

    for table in tables['name']:
        data = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)

        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        data.set_index('date', inplace=True)
        clean_table_name = '-'.join(table.split('_')[:2])
        tables_data[clean_table_name] = data
    conn.close()

    return tables_data