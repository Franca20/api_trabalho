from app import app
from flask import render_template, request, jsonify
from pathlib import Path
from app.utils import load_data

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'data/dados.json'
data = load_data(DATA_FILE)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data)

@app.route('/api/carregamento', methods=['GET'])
def get_carregamento():
    carregamento_file = BASE_DIR / 'data/dados_carregamento.json'
    carregamento = load_data(carregamento_file)
    return jsonify(carregamento)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/motoristas')
def motoristas():
    return render_template('motoristas.html')
