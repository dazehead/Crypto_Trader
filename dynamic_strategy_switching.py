import wrapper
import os
import strategies 
import database_interaction
from backtest import run_basic_backtest
from strategies.efratio import EFratio
from strategies.vwap import Vwap
from strategies.rsi import RSI
from strategies.macd import MACD

granularity = 'ONE_MINUTE'
symbols = ['BTC-USD']
tables_data = database_interaction.get_historical_from_db(granularity=granularity, symbols=symbols)

indicators_map = {
    'bull': [],
    'bear': [],
    'consolidation': []
}

indicators_map_strategies = {
    'bull': [RSI, Vwap],
    'bear': [MACD, EFratio],
    'consolidation': []
}

def detect_market_condition(symbol, data):
    if data.empty:
        print(f"No data available for {symbol}.")
        return 'consolidation'  # or any default value you prefer

    ma_200 = data['close'].rolling(window=200).mean().iloc[-1]
    current_price = data['close'].iloc[-1]

    if current_price > ma_200:
        indicators_map['bull'].append(symbol)
        return 'bull'
    elif current_price < ma_200:
        indicators_map['bear'].append(symbol)
        return 'bear'
    else:
        indicators_map['consolidation'].append(symbol)
        return 'consolidation'

# Function to get strategy names for display
def get_strategy_names(strategy_classes):
    return [strategy.__name__ for strategy in strategy_classes]

for key, value in tables_data.items():
    current_market = detect_market_condition(key, value)
    print(f"For {key}, current market condition is {current_market}.")

    strategies_to_test = indicators_map_strategies.get(current_market, [])
    for strategy in strategies_to_test:
        run_basic_backtest(strategy)

# Printing strategies with names
formatted_strategies = {
    key: get_strategy_names(strategies_list)
    for key, strategies_list in indicators_map_strategies.items()
}

print(f"indicators_map: {indicators_map}")
print(f"Formatted indicators_map_strategies: {formatted_strategies}")
