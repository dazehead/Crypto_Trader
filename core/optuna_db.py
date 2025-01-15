import optuna
import os
import pandas as pd

# Path to your Optuna database
db_path = os.getenv('DATABASE_PATH')
if not db_path:
    raise ValueError("DATABASE_PATH environment variable is not set.")
optuna_db = f"sqlite:///{db_path}/hyper_optuna.db"

def get_best(storage_path):
    all_data = []
    try:
        # Connect to Optuna storage
        storage = optuna.storages.RDBStorage(url=storage_path)

        # Get all study summaries
        study_summaries = optuna.get_all_study_summaries(storage=storage)

        for study_summary in study_summaries:
            study_name = study_summary.study_name
            study = optuna.load_study(storage=storage, study_name=study_name)

            # Get trials with value > 0.50
            best_trials = [
                trial for trial in study.trials
                if trial.value is not None and trial.value > 0.50
            ]

            for trial in best_trials:
                all_data.append({
                    "study_name": study_name,
                    "trial_id": trial.number,
                    "value": trial.value,
                    "params": trial.params
                })
    except Exception as e:
        print(f"An error occurred: {e}")
    return pd.DataFrame(all_data)

# Retrieve best trials
best_trials_df = get_best(optuna_db)
# Export to CSV
best_trials_df.to_csv('best_trials.csv', index=False)

print(best_trials_df)
