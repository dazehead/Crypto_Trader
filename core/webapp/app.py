from flask import Flask, request, jsonify
from flask_cors import CORS
from ..backtest import Backtest
from ..strategies.single.rsi import RSI
from ..strategies.gpu_optimized.rsi_adx_np import RSI_ADX_NP
import base64
import plotly.io as pio

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}})

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {str(e)}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500

def to_png(fig):
    try:
        img_bytes = pio.to_image(fig, format="png")
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        app.logger.error(f"Error converting graph to PNG: {str(e)}")
        raise ValueError("Graph conversion failed.")

@app.route('/api/backtest', methods=['POST'])
def backtest():
    params = request.json
    app.logger.info(f"Received params: {params}")

    strategy_mapping = {
        "RSI": RSI,
        "RSI_ADX_NP": RSI_ADX_NP,
    }
    strategy_obj = strategy_mapping[params["strategy_obj"]]

    backtest_instance = Backtest()
    try:
        stats, graph_base64 = backtest_instance.run_basic_backtest(
            symbol=[params["symbol"]],
            granularity=params["granularity"],
            strategy_obj=strategy_obj,
            num_days=params["num_days"],
            sizing=params["sizing"],
            best_params=params["best_params"],
            graph_callback=to_png
        )
    except Exception as e:
        app.logger.error(f"Backtest failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

    if stats is None:
        return jsonify({"status": "error", "message": "Backtest returned no stats"}), 500

    return jsonify({"status": "success", "stats": stats, "graph": graph_base64})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
