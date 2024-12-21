from flask import Flask, request, jsonify
from flask_cors import CORS
from ..backtest import Backtest
from ..strategies.single.rsi import RSI
from ..strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
import base64
import io
from io import BytesIO
import plotly.io as pio

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080"],  # Add your frontend's origin here
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
  

@app.route('/api/backtest', methods=['POST'])
def backtest():
    params = request.json
    print("Received params:", params)
    try:
        num_days = int(params["num_days"])  
        print(num_days)
    except ValueError as e:
        print(num_days)
        raise ValueError(f"Invalid parameter type for num_days: {e}")

    if not isinstance(params["sizing"], bool):
        sizing = params["sizing"]
        raise ValueError(f"Invalid parameter type for sizing: Expected bool, got {type(sizing)}")
        
    strategy_mapping = {
            "RSI": RSI,
            "RSI_ADX_GPU": RSI_ADX_GPU,
    }
    strategy_obj = params.get("strategy_obj")

    if isinstance(strategy_obj, str) and strategy_obj in strategy_mapping:
        strategy_obj = strategy_mapping[strategy_obj]
    else:
        raise ValueError(f"Invalid strategy_obj: {strategy_obj}")

    
    def to_png(fig):
        try:
            img_bytes = pio.to_image(fig, format="png")
            graph_base64 = base64.b64encode(img_bytes).decode('utf-8')

            return graph_base64
        except Exception as e:
            raise ValueError(f"Error converting graph to base64: {e}")

    backtest_instance = Backtest()

    

    print("symbol = ", params["symbol"])
    print("granularity = ", params["granularity"])
    print("strategy object = ", strategy_obj)
    print("num_days = ", num_days)
    print("sizing = ", params["sizing"])
    print("best_params = ", params["best_params"])
    print("graph_callback = ", to_png)

    try:
        stats, graph_base64 = backtest_instance.run_basic_backtest(
            symbol=params["symbol"],
            granularity=params["granularity"],
            strategy_obj=strategy_obj,
            num_days=num_days,
            sizing=params["sizing"],
            best_params=params["best_params"],
            graph_callback=to_png
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    if stats is None:
        return jsonify({"status": "error", "message": "Backtest returned no stats"}), 500
    print("Generated graph base64:", graph_base64[:100])  # Log the first 100 chars

    return jsonify({
        "status": "success",
        "stats": stats,
        "graph": graph_base64
    })



# @app.route('/api/livetrade', methods=['POST'])
# def livetrade():
# 
#     params = request.json
#     results = start_live_trading(params)
#     return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
