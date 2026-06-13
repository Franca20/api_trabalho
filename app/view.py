from app import app
from flask import render_template, request, jsonify
from pathlib import Path
from app.utils import load_data

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'data/descarregamento.json'
data = load_data(DATA_FILE)

@app.route('/api/descarregar', methods=['GET'])
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data)

@app.route('/api/carregamento', methods=['GET'])
def get_carregamento():
    carregamento_file = BASE_DIR / 'data/carregamento.json'
    carregamento = load_data(carregamento_file)
    return jsonify(carregamento)

@app.route('/')
def home():
    return render_template('descarregar.html')

@app.route('/carregar')
def carregar():
    return render_template('carregar.html')

#  testes com api em js

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/api/teste', methods=['GET'])
def get_teste():
    return jsonify({"message": "Teste bem-sucedido!", "status": "success"})