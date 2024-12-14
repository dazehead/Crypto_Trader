from flask import Flask, request, jsonify
from flask_cors import CORS
from backtest import Backtest

app = Flask(__name__)
CORS(app)  

@app.route('/api/backtest', methods=['POST'])
def backtest():
    params = request.json

    stats, graph_base64 = Backtest.run_basic_backtest(*params, graph_callback=True)

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
    app.run(debug=True)
