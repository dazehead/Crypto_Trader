from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import core.utils as utils
import datetime as dt
import numpy as np
import core.database_interaction as database_interaction
import time
import gc
import gc
import io
import base64
from coinbase.rest import RESTClient
from core.strategies.strategy import Strategy
from core.strategies.single.efratio import EFratio
from core.strategies.single.vwap import Vwap
from core.strategies.single.rsi import RSI
from core.strategies.single.atr import ATR
from core.strategies.single.macd import MACD
from core.strategies.single.kama import Kama
from core.strategies.single.adx import ADX
from core.strategies.single.bollinger import BollingerBands
from core.strategies.double.rsi_adx import RSI_ADX
from core.strategies.combined_strategy import Combined_Strategy
from core.strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
from core.strategies.gpu_optimized.rsi_adx_np import RSI_ADX_NP
from core.strategies.gpu_optimized.rsi_bollinger_np import BollingerBands_RSI
from core.risk import Risk_Handler
from core.log import LinkedList
from core.hyper import Hyper
from core.backtest import Backtest
import plotly
from io import BytesIO
from PIL import Image
#pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)
import logging
logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("numpy").setLevel(logging.WARNING)


logging.basicConfig(level=logging.INFO) 

class AI_Backtest(Backtest):
    def __init__(self):
        super().__init__()
    def run_ml_tests(self, strategy_class, param_ranges, historical_data, train_test_split=0.7):
        """
        Integrate ML to predict future behavior in the optimization tests.

        Args:
            strategy_class: The strategy class to test (e.g., RSI_ADX_GPU).
            param_ranges: Dictionary of hyperparameter ranges for optimization.
            historical_data: Dictionary containing OHLC data for symbols.
            train_test_split: Proportion of data to use for training (default: 70% train, 30% test).
        """
        results = []
        risk = Risk_Handler()

        for symbol, data in historical_data.items():
            try:
                if not {'open', 'high', 'low', 'close'}.issubset(data.columns):
                    logging.warning(f"Data for {symbol} does not contain OHLC columns. Skipping.")
                    continue

                total_len = len(data)
                train_len = int(total_len * train_test_split)

                # Extract features and labels
                features = self.extract_features(data)
                labels = self.generate_labels(data)

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    features, labels, train_size=train_test_split, shuffle=False
                )

                # Train ML model
                model = RandomForestClassifier(random_state=42)
                model.fit(X_train, y_train)

                # Evaluate on test data
                predictions = model.predict(X_test)
                report = classification_report(y_test, predictions)
                logging.info(f"Classification Report for {symbol}:\n{report}")

                # Integrate predictions into backtesting
                data['ml_signal'] = np.nan
                data.loc[X_test.index, 'ml_signal'] = predictions

                strat_test = strategy_class(
                    dict_df={symbol: data},
                    risk_object=risk,
                    with_sizing=True
                )
                strat_test.generate_backtest()
                stats = strat_test.portfolio.stats(silence_warnings=True).to_dict()
                stats.update({"symbol": symbol})
                results.append(stats)

            except Exception as e:
                logging.error(f"Error processing {symbol}: {e}", exc_info=True)

        # Save results
        results_df = pd.DataFrame(results)
        database_interaction.export_optimization_results(results_df)
        return results_df

    def extract_features(self, data):
        """Extract RSI and ADX as features for ML."""
        data['rsi'] = self.calculate_rsi(data['close'])
        data['adx'] = self.calculate_adx(data['high'], data['low'], data['close'])
        return data[['rsi', 'adx']].dropna()

    def generate_labels(self, data):
        """Generate labels for ML (e.g., 1 for buy, -1 for sell, 0 for hold)."""
        future_returns = data['close'].pct_change().shift(-1)
        labels = np.where(future_returns > 0, 1, np.where(future_returns < 0, -1, 0))
        return pd.Series(labels, index=data.index).dropna()

    def calculate_rsi(self, close, rsi_window=14):
        delta = close.diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(rsi_window).mean()
        avg_loss = loss.rolling(rsi_window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_adx(self, high, low, close, adx_time_period=14):
        tr1 = (high - low).abs()
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        plus_dm = high.diff().clip(lower=0)
        minus_dm = low.diff().clip(upper=0).abs()

        atr = true_range.rolling(adx_time_period).mean()
        plus_di = 100 * plus_dm.rolling(adx_time_period).mean() / atr
        minus_di = 100 * minus_dm.rolling(adx_time_period).mean() / atr

        dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
        adx = dx.rolling(adx_time_period).mean()
        return adx


if __name__ == "__main__":
    # Example historical data
    historical_data = {
        'BTC-USD': pd.DataFrame({
            'open': [...], 'high': [...], 'low': [...], 'close': [...],  # OHLC data
        }),
        # Add other symbols
    }

    backtest = AI_Backtest()
    strategy = RSI_ADX_GPU(dict_df=None)

    param_ranges = {
        'rsi_buy_threshold': [20, 30],
        'rsi_sell_threshold': [70, 80],
        'adx_threshold': [20, 30]
    }

    # Run backtests
    results = backtest.run_ml_tests(
        strategy_class=RSI_ADX_GPU,
        param_ranges=param_ranges,
        historical_data=historical_data
    )
    print(results)