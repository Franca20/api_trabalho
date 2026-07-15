import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
from flask import jsonify, render_template, request

from app import app
from app.utils import load_data, save_data

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'data/descarregamento.json'
COMPLETED_FILE = BASE_DIR / 'data/descarregamento_concluidos.json'


def get_pending_data():
    source_data = load_data(DATA_FILE)
    completed_data = load_data(COMPLETED_FILE)
    completed_ids = {str(item.get('LT', '')).strip() for item in completed_data if item.get('LT')}
    return [item for item in source_data if str(item.get('LT', '')).strip() not in completed_ids]


@app.route('/api/descarregar', methods=['GET'])
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(get_pending_data())


@app.route('/api/descarregar/concluir', methods=['POST'])
def concluir_descarregamento():
    payload = request.get_json(silent=True) or {}
    item = payload.get('item') or {}

    if not item:
        return jsonify({'success': False, 'message': 'Nenhum motorista informado.'}), 400

    completed_data = load_data(COMPLETED_FILE)
    item_id = str(item.get('LT', '')).strip()
    completed_ids = {str(existing.get('LT', '')).strip() for existing in completed_data if existing.get('LT')}

    if item_id and item_id in completed_ids:
        return jsonify({'success': True, 'message': 'Motorista já estava marcado.', 'already_completed': True})

    completed_entry = {
        **item,
        'status': 'concluido',
        'concluido_em': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    completed_data.append(completed_entry)
    save_data(COMPLETED_FILE, completed_data)

    return jsonify({'success': True, 'message': 'Motorista marcado como concluído.', 'completed': completed_entry})


@app.route('/api/concluidos', methods=['GET'])
def get_concluidos():
    return jsonify(load_data(COMPLETED_FILE))


@app.route('/api/carregamento', methods=['GET'])
def get_carregamento():
    carregamento_file = BASE_DIR / 'data/carregamento.json'
    carregamento = load_data(carregamento_file)
    return jsonify(carregamento)


@app.route('/')
def home():
    return render_template('descarregar.html')


@app.route('/concluidos')
def concluidos():
    return render_template('concluidos.html')


@app.route('/carregar')
def carregar():
    return render_template('carregar.html')


@app.route('/qrcode')
def qrcode_page():
    return render_template('qrcode.html')


@app.route('/api/lt/qr', methods=['POST'])
def generate_lt_qr():
    payload = request.get_json(silent=True) or {}
    lt_value = str(payload.get('lt', '') or '').strip().upper()

    if not lt_value:
        return jsonify({'success': False, 'message': 'Informe a LT do motorista.'}), 400

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(lt_value)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format='PNG')
    encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return jsonify({'success': True, 'lt': lt_value, 'qr_image': encoded, 'qr_text': lt_value})


#  testes com api em js

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/api/teste', methods=['GET'])
def get_teste():
    return jsonify({'message': 'Teste bem-sucedido!', 'status': 'success'})