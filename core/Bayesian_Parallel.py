import multiprocessing
import optuna
from core.backtest import Backtest
from core.strategies.gpu_optimized.GPU.rsi_adx_gpu import RSI_ADX_GPU
import core.database_interaction as database_interaction
from core.strategies.gpu_optimized.NP.bollinger_vwap import Bollinger_VWAP
import sqlite3 as sql
from dotenv import load_dotenv
import os
import time

backtest_instance = Backtest()
load_dotenv()

db_path = os.getenv('DATABASE_PATH')
print("DATABASE_PATH : ", db_path)
def optimize_worker(strategy_class, symbol, granularity, db_path, n_trials):
    study_name = f"{strategy_class.__name__}_{symbol}_{granularity}"
    trial_durations = []

    def objective(trial):
        start_time = time.time()
        params = {
            'rsi_window': trial.suggest_int('rsi_window', 5, 50),
            'buy_threshold': trial.suggest_int('buy_threshold', 10, 30),
            'sell_threshold': trial.suggest_int('sell_threshold', 70, 90),
            'adx_time_period': trial.suggest_int('adx_time_period', 10, 50),
            'adx_buy_threshold': trial.suggest_int('adx_buy_threshold', 20, 50),
        }

        stats = backtest_instance.run_optuna_backtest(
            symbol=symbol,
            granularity=granularity,
            strategy_obj=strategy_class,
            num_days=365,
            sizing=True,
            params=params
        )

        return stats.get('Total Return [%]', -1)

    try:
        study = optuna.create_study(
            direction='maximize',
            study_name=study_name,
            storage=f"sqlite:///{db_path}/hyper_optuna.db"
        )
    except optuna.exceptions.DuplicatedStudyError:
        study = optuna.load_study(
            study_name=study_name,
            storage=f"sqlite:///{db_path}/hyper_optuna.db"
        )

    study.optimize(objective, n_trials=n_trials)

    if trial_durations:
        avg_trial_time = sum(trial_durations) / len(trial_durations)
        total_estimated_time = avg_trial_time * n_trials
        print(f"Estimated time for '{study_name}': {total_estimated_time:.2f} seconds.")
    else:
        print(f"No trials completed for '{study_name}'.")

# Multiprocessing
if __name__ == "__main__":
    symbols = ['BTC-USD', 'ETH-USD'] #, 'DOGE-USD', 'SHIB-USD', 'AVAX-USD', 'BCH-USD', 'LINK-USD', 'UNI-USD', 'LTC-USD', 'XLM-USD', 'ETC-USD', 'AAVE-USD', 'XTZ-USD', 'COMP-USD'
    granularity = ['ONE_MINUTE','FIVE_MINUTE','FIFTEEN_MINUTE','THIRTY_MINUTE','ONE_HOUR','TWO_HOUR','SIX_HOUR','ONE_DAY']
     # Example granularities
    n_trials = 100
    num_workers = 4  # Adjust based on available CPU cores

    pool = multiprocessing.Pool(processes=num_workers)
    tasks = [
        (RSI_ADX_GPU, symbol, gran, db_path, n_trials)
        for symbol in symbols
        for gran in granularity
    ]
    pool.starmap(optimize_worker, tasks)
    pool.close()
    pool.join()
