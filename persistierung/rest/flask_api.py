from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

@app.route('/bottles/count', methods=['GET'])
def bottle_count():
    df = pd.read_csv('../database/data.csv')
    return jsonify(count=len(df))

@app.route('/bottles/latest', methods=['GET'])
def latest_bottle():
    df = pd.read_csv('../database/data.csv')
    return df.tail(1).to_json(orient='records')

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, threaded=True)