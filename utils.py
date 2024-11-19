import pandas as pd
import datetime as dt
import numpy as np
import sqlite3 as sql
import inspect
import re
import sys
import time
from numba import njit
pd.set_option('future.no_silent_downcasting', True)


@njit
def format_signals(signals):
    """
    Formats signals to avoid double buys or sells.
    Optimized using NumPy arrays with a loop.
    """
    formatted_signals = np.zeros_like(signals)
    in_position = False

    for i in range(len(signals)):
        if signals[i] == 1 and not in_position:
            formatted_signals[i] = 1
            in_position = True
        elif signals[i] == -1 and in_position:
            formatted_signals[i] = -1
            in_position = False
        # Else, no change; formatted_signals[i] remains 0
        # in_position remains the same

    return formatted_signals

@njit
def calculate_with_sizing_numba(signal, close, percent_to_size):
    n = len(signal)
    new_signal = signal.copy()
    saved_close = 0.0
    tracking = False

    for i in range(n):
        if signal[i] == 1 and not tracking:
            saved_close = close[i]
            tracking = True
        elif tracking:
            target_close = saved_close * (1 + percent_to_size)

            if signal[i] == 0:
                if close[i] >= target_close:
                    new_signal[i] = 1
                    saved_close = close[i]
                elif close[i] <= target_close * (1 - (percent_to_size * 2)):
                    saved_close = close[i]

            if signal[i] == -1:
                tracking = False
                saved_close = 0.0
    return new_signal

def progress_bar_with_eta(progress, data, start_time, bar_length=50):
    total = len(data)
    progress +=1

    elapsed_time = time.time() - start_time  # Time passed since start
    avg_time_per_item = elapsed_time / progress if progress > 0 else 0
    eta = avg_time_per_item * (total - progress)  # Estimate remaining time in seconds

    # Format ETA as minutes and seconds
    eta_minutes = int(eta // 60)
    eta_seconds = int(eta % 60)

    # Calculate percentage and progress bar
    if progress >= total:
        percent = 100
        bar = '#' * bar_length
        eta_minutes = 0
        eta_seconds = 0
    else:
        percent = int((progress / total) * 100)
        bar = ('#' * int(bar_length * (progress / total))).ljust(bar_length)

    # Display the progress bar and ETA
    sys.stdout.write(f'\r|{bar}| {percent}% Complete | ETA: {eta_minutes:02d}:{eta_seconds:02d} remaining')
    sys.stdout.flush()

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
 

