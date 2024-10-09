import datetime as dt
import pandas as pd
import utils


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


def fetch_data_with_retries(client, symbol, start, end, granularity, max_retries=10000):
    from datetime import datetime, timedelta

    retry_count = 0
    df = pd.DataFrame()
    original_start = start

    while retry_count < max_retries:
        btc_candles = client.get_candles(
            product_id=symbol,
            start=start,
            end=end,
            granularity=granularity
        )
        df = utils.to_df(btc_candles)

        if not df.empty:
            break  # Data found, exit the loop
        else:
            # Decrement the start date by one month (or any preferred interval)
            return df
            # print(df)
            # start_datetime = datetime.fromisoformat(str(start))
            # print(type(start_datetime))
            # new_start_datetime = start_datetime - timedelta(days=30)
            # start = new_start_datetime.isoformat()
            # retry_count += 1
            # print(f"No data for {symbol} between {start} and {end}. Retrying with earlier start date: {start}")

    if df.empty:
        print(f"Unable to retrieve data for {symbol} after {max_retries} retries starting from {original_start}.")
    return df



def get_candles(client, symbols: list, timestamps, granularity: str):
    """Function that gets candles for every pair of timestamps and combines them all."""
    combined_data = {}
    for symbol in symbols:
        print(f'...getting data for {symbol}')
        combined_df = pd.DataFrame()

        for pair in timestamps:
            start, end = pair
            df = fetch_data_with_retries(client, symbol, start, end, granularity)
            if df.empty:
                break
            combined_df = pd.concat([combined_df, df], ignore_index=True)

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




