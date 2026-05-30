from app import app
from flask import render_template, request, jsonify
from pathlib import Path
from app.utils import load_data

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'data/dados.json'
data = load_data(DATA_FILE)

@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify(data)

@app.route("/")
def home():
    return render_template("index.html")