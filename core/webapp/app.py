from flask import Flask, request, jsonify
from flask_cors import CORS
from backtest import Backtest
import io
import base64
from io import BytesIO

app = Flask(__name__)
CORS(app)  

@app.route('/api/backtest', methods=['POST'])
def backtest():
    params = request.json

    def to_png(fig):
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png')
        img_buf.seek(0)
        graph_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
        img_buf.close()
        return graph_base64

    stats, graph_base64 = Backtest.run_basic_backtest(*params, graph_callback=to_png, to_web=True)

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
