import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import qrcode
from flask import jsonify, render_template, request

from app import app
from app.db import fetch_descarregamento_data
from app.utils import save_data
from app.concluidos_bd import fetch_concluidos_by_date, save_concluded
from app.escrever_dados_bd import main
import tempfile

BASE_DIR = Path(__file__).parent


def get_pending_data():
    source_data = fetch_descarregamento_data()
    completed_data = fetch_concluidos_by_date()
    completed_ids = {str(item.get('LT', '')).strip() for item in completed_data if item.get('LT')}
    return [item for item in source_data if str(item.get('LT', '')).strip() not in completed_ids]


@app.route('/api/descarregar', methods=['GET'])
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(get_pending_data())


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/descarregar/concluir', methods=['POST'])
def concluir_descarregamento():
    payload = request.get_json(silent=True) or {}
    item = payload.get('item') or {}

    if not item:
        return jsonify({'success': False, 'message': 'Nenhum motorista informado.'}), 400

    completed_data = fetch_concluidos_by_date()
    item_id = str(item.get('LT', '')).strip()
    completed_ids = {str(existing.get('LT', '')).strip() for existing in completed_data if existing.get('LT')}

    if item_id and item_id in completed_ids:
        return jsonify({'success': True, 'message': 'Motorista já estava marcado.', 'already_completed': True})

    timezone_sp = ZoneInfo('America/Sao_Paulo')
    concluded_at = datetime.now(timezone_sp)

    payload = {
        **item,
        'LT': item.get('LT') or item.get('lt'),
        'Station Name': item.get('Station Name') or item.get('station'),
        'vehicle_plate_number': item.get('vehicle_plate_number') or (','.join(item.get('plates', [])) if isinstance(item.get('plates'), list) else None),
        'Driver': item.get('Driver') or item.get('driver'),
        'Schedule Arrival Time': item.get('Schedule Arrival Time') or item.get('schedule'),
        'TO': item.get('TO') or item.get('to'),
        'status': 'concluido',
        'concluido_em': concluded_at.strftime('%d/%m/%Y %H:%M:%S'),
    }

    try:
        saved = save_concluded(payload, concluded_at=concluded_at)
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Erro ao salvar no banco: {exc}'}), 500

    return jsonify({'success': True, 'message': 'Motorista marcado como concluído.', 'completed': saved})

@app.route('/api/concluidos', methods=['GET'])
def get_concluidos():
    concluidos = fetch_concluidos_by_date()
    return jsonify(concluidos)


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


@app.route('/extrair-csv')
def extrair_csv_page():
    return render_template('extrair_csv.html')



@app.route('/api/extrair-csv', methods=['POST'])
def api_extrair_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado.'}), 400

    arquivo = request.files['file']
    if arquivo.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado.'}), 400

    # cria arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        arquivo.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        main(tmp_path)   # usa seu main sem mudar nada
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Erro ao processar CSV: {exc}'}), 500

    return jsonify({'success': True, 'message': 'Dados extraídos e salvos no banco'})

@app.route('/api/limpar-descarregamento', methods=['POST'])
def limpar_descarregamento():
    try:
        # limpar o JSON usado apenas como fallback local
        save_data(BASE_DIR / 'data' / 'descarregamento.json', [])
        return jsonify({'success': True, 'message': 'descarregamento.json limpo com sucesso.'})
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Erro ao limpar JSON: {exc}'}), 500


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

##############################################################################################


@app.route('/mapa bolsao')
def mapa_bolsao():
    return render_template('mapa_bolsao.html')

#  testes com api em js

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/api/teste', methods=['GET'])
def get_teste():
    return jsonify({'message': 'Teste bem-sucedido!', 'status': 'success'})