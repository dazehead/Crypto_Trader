import optuna
from core.backtest import Backtest
from core.strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
import sqlite3 as sql
from dotenv import load_dotenv
import os

load_dotenv()

db_path = os.getenv('DATABASE_PATH')
print("DATABASE_PATH : ", db_path)  # Ensure the correct database path is printed
study_name = "RSI_ADX_GPU_Optimization2"

class BacktestWithBayesian(Backtest):
    def run_bayesian_optimization(self, strategy_class, n_trials=100):
        def objective(trial):
            # Define parameter ranges
            params = {
                'rsi_window': trial.suggest_int('rsi_window', 5, 50),
                'buy_threshold': trial.suggest_int('buy_threshold', 10, 30),
                'sell_threshold': trial.suggest_int('sell_threshold', 70, 90),
                'adx_time_period': trial.suggest_int('adx_time_period', 10, 50),
                'adx_buy_threshold': trial.suggest_int('adx_buy_threshold', 20, 50),
            }

            # Run Optuna backtest for the suggested parameters
            stats = self.run_optuna_backtest(
                symbol='BTC-USD',
                granularity='ONE_HOUR',
                strategy_obj=strategy_class,
                num_days=365,
                sizing=True,
                params=params
            )

            # Objective: Maximize total return
            return stats.get('Total Return [%]', -1)  # Default to -1 if no stats generated

        # Run the optimization
        try:
            study = optuna.create_study(
                direction='maximize', 
                study_name=study_name, 
                storage=f"sqlite:///{db_path}/new_backtest.db"
            )
            print(f"Study '{study_name}' created successfully.")
        except optuna.exceptions.DuplicatedStudyError:
            print(f"Study '{study_name}' already exists. Attempting to load it...")
            # Load the existing study if it already exists
            study = optuna.load_study(
                study_name=study_name, 
                storage=f"sqlite:///{db_path}/new_backtest.db"
            )

        # Ensure the study variable is defined
        if not study:
            raise RuntimeError("Failed to create or load the study.")

        study.optimize(objective, n_trials=n_trials)

        # Export the results
        self.export_optimization_results_to_db(study, strategy_class)

    def export_optimization_results_to_db(self, study, strategy_class):
        """Export Bayesian optimization results to the database."""
        conn = sql.connect(f'{db_path}/new_backtest.db')
        table_name = f"OptunaOptimization_{strategy_class.__name__}"

        # Create table if it doesn't exist
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                trial_id INTEGER PRIMARY KEY,
                params TEXT,
                value REAL
            )
        """)

        # Insert the results
        for trial in study.trials:
            params = str(trial.params)
            value = trial.value
            
            # Check if trial_id already exists
            cursor = conn.execute(f"SELECT COUNT(1) FROM {table_name} WHERE trial_id = ?", (trial.number,))
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                # If trial_id doesn't exist, insert it
                conn.execute(f"""
                    INSERT INTO "{table_name}" (trial_id, params, value)
                    VALUES (?, ?, ?)
                """, (trial.number, params, value))

        conn.commit()
        conn.close()


backtest_instance = BacktestWithBayesian()
backtest_instance.run_bayesian_optimization(RSI_ADX_GPU, n_trials=200)
