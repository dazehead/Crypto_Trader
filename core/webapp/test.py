from flask import Flask, request, jsonify
from flask_cors import CORS
from ..backtest import Backtest
from ..strategies.single.rsi import RSI
import io
import base64
from io import BytesIO

test_params = {
    "symbol": ["BTC-USD"],
    "granularity": "ONE_MINUTE",
    "num_days": 100,
    "sizing": True,
    "strategy_obj": "RSI",
    "best_params": False
}

strategy_obj = test_params.get("strategy_obj")
strategy_mapping = {"RSI": RSI}
if strategy_obj in strategy_mapping:
    strategy_obj = strategy_mapping[strategy_obj]

backtest_instance = Backtest()

def to_png(fig):
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png')
    img_buf.seek(0)
    graph_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
    img_buf.close()
    return graph_base64

try:
    stats, graph_base64 = backtest_instance.run_basic_backtest(
        symbol=test_params["symbol"],
        granularity=test_params["granularity"],
        strategy_obj=strategy_obj,
        num_days=test_params["num_days"],
        sizing=test_params["sizing"],
        best_params=test_params["best_params"],
        graph_callback=to_png
    )
    print("Stats:", stats)
except Exception as e:
    print(f"Error running backtest: {e}")
