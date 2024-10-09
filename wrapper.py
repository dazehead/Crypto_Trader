import datetime as dt
import pandas as pd
import utils
import sqlite3 as sql


def get_unix_times(granularity:str, days: int = None):
    # Mapping each timeframe to its equivalent seconds value
    timeframe_seconds = {
        'ONE_MINUTE': 60,
        'FIVE_MINUTE': 300,
        'FIFTEEN_MINUTE': 900,
        'THIRTY_MINUTE': 1800,
        'ONE_HOUR': 3600,
        'TWO_HOUR': 7200,
        'SIX_HOUR': 21600,
        'ONE_DAY': 86400
    }

    # Check if the granularity provided is valid
    if granularity not in timeframe_seconds:
        raise ValueError(f"Invalid granularity '{granularity}'. Must be one of {list(timeframe_seconds.keys())}")

    # Get the current timestamp
    now = int(dt.datetime.now().timestamp())
    limit = 350  # Max number of candles we can fetch
    granularity_seconds = timeframe_seconds[granularity]  # Get the seconds per timeframe unit

    # Calculate max time range for the given granularity
    max_time_range_seconds = limit * granularity_seconds
    timestamp_max_range = now - max_time_range_seconds

    # If days are specified, we need to generate pairs of (now, timestamp_max_range) until the number of days is covered
    if days:
        results = []
        seconds_in_day = 86400  # 1 day in seconds
        total_seconds_to_cover = days * seconds_in_day
        remaining_seconds = total_seconds_to_cover

        # Loop until we cover the requested number of days
        while remaining_seconds > 0:
            # Calculate how much time we can cover in this iteration
            current_time_range_seconds = min(max_time_range_seconds, remaining_seconds)

            # Calculate the new timestamp range
            timestamp_max_range = now - current_time_range_seconds

            # Append the pair (now, timestamp_max_range) to the results
            results.append((timestamp_max_range, now))

            # Update 'now' and the remaining seconds
            now = timestamp_max_range
            remaining_seconds -= max_time_range_seconds
        return results[::-1]

    # If no days are specified, return a single pair of (now, timestamp_max_range)
    return [(timestamp_max_range, now)]


def get_data_from_db(symbol, granularity):
    """Retrieve existing data for a symbol from the database."""
    conn = sql.connect(f'database/{granularity}.db')
    cursor = conn.cursor()
    symbol_for_table = symbol.replace('-', '_')
    # Get the list of tables that contain the symbol
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (f'{symbol_for_table}_%',))
    tables = cursor.fetchall()
    combined_df = pd.DataFrame()
    for table in tables:
        table_name = table[0]
        data = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        #print(data.head())
        data['date'] = pd.to_datetime(data['date'])
        data.set_index('date', inplace=True)
        combined_df = pd.concat([combined_df, data])
    conn.close()
    if not combined_df.empty:
        combined_df = combined_df.sort_index()
    return combined_df

def fetch_data_with_retries(client, symbol, start_unix, end_unix, granularity, max_retries=5):
    retry_count = 0
    df = pd.DataFrame()
    original_start = start_unix

    while retry_count < max_retries:
        btc_candles = client.get_candles(
            product_id=symbol,
            start=start_unix,
            end=end_unix,
            granularity=granularity
        )
        df = utils.to_df(btc_candles)

        if not df.empty:
            break  # Data found, exit the loop
        else:
            print(pd.to_datetime(start_unix, unit='s'))
            retry_count += 1
            return df

    if df.empty:
        print(f"Unable to retrieve data for {symbol} after {max_retries} retries starting from {original_start}.")
    return df


def get_missing_unix_ranges(desired_start_unix, desired_end_unix, existing_start_unix, existing_end_unix):
    """Compute missing UNIX time ranges that are not covered by existing data."""
    missing_ranges = []

    if desired_end_unix <= existing_start_unix or desired_start_unix >= existing_end_unix:
        # No overlap, entire desired range is missing
        missing_ranges.append((desired_start_unix, desired_end_unix))
    else:
        if desired_start_unix < existing_start_unix:
            # Missing from desired_start to existing_start
            missing_ranges.append((desired_start_unix, existing_start_unix))
        if desired_end_unix > existing_end_unix:
            # Missing from existing_end to desired_end
            missing_ranges.append((existing_end_unix, desired_end_unix))
        # If desired_range is within existing_range, no missing ranges

    return missing_ranges


def get_candles(client, symbols: list, timestamps, granularity: str):
    """Function that gets candles for every pair of timestamps and combines them all, avoiding redundant data fetching."""
    combined_data = {}
    for symbol in symbols:
        print(f'...getting data for {symbol}')
        combined_df = pd.DataFrame()

        # Get existing data from the database
        existing_data = get_data_from_db(symbol, granularity)

        if not existing_data.empty:
            existing_start_unix = int(existing_data.index.min().timestamp())
            existing_end_unix = int(existing_data.index.max().timestamp())
        else:
            existing_start_unix = None
            existing_end_unix = None

        # For each desired date range, adjust the range to exclude existing data
        missing_date_ranges = []
        for pair in timestamps:
            desired_start_unix, desired_end_unix = pair

            if existing_start_unix is not None and existing_end_unix is not None:
                missing_ranges = get_missing_unix_ranges(desired_start_unix, desired_end_unix, existing_start_unix, existing_end_unix)
            else:
                missing_ranges = [(desired_start_unix, desired_end_unix)]

            missing_date_ranges.extend(missing_ranges)

        # Now fetch data for missing date ranges
        for missing_range in missing_date_ranges:
            start_unix, end_unix = missing_range
            df = fetch_data_with_retries(client, symbol, start_unix, end_unix, granularity)
            if df.empty:
                continue  # Or handle as needed
            combined_df = pd.concat([combined_df, df], ignore_index=True)

        # Combine with existing data
        if not existing_data.empty:
            combined_df = pd.concat([combined_df, existing_data.reset_index()], ignore_index=True)

        if not combined_df.empty:
            sorted_df = combined_df.sort_values(by='date', ascending=True).reset_index(drop=True)
            columns_to_convert = ['low', 'high', 'open', 'close', 'volume']
            for col in columns_to_convert:
                sorted_df[col] = pd.to_numeric(sorted_df[col], errors='coerce')
            sorted_df.set_index('date', inplace=True)
            combined_data[symbol] = sorted_df
        else:
            print(f"No data available for {symbol} in the specified date ranges.")

    return combined_data




