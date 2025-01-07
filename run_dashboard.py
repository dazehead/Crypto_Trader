from optuna_dashboard import app

# Set the storage URL for the dashboard
app.storage_url = "sqlite:///E:/database/new_backtest.db"

# Export the WSGI application
application = app
