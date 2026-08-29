import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
from flask import jsonify, render_template, request

from app import app
from app.db import fetch_vagas_assignments, remove_vaga_assignment, save_vaga_assignment
from app.utils import get_data_path, load_data, save_data
from app.concluidos_bd import PARANA_TIMEZONE, clear_concluidos, fetch_concluidos_by_date, save_concluded
from app.data.extrair_descarregamento import extrair_dados_filtrados
import tempfile

BASE_DIR = Path(__file__).parent


def get_pending_data():
    source_data = load_data(get_data_path('descarregamento.json'))
    if not isinstance(source_data, list):
        return []

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

    concluded_at = datetime.now(PARANA_TIMEZONE)

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
        if item_id:
            remove_vaga_assignment(lt=item_id)
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Erro ao salvar no arquivo JSON: {exc}'}), 500

    return jsonify({'success': True, 'message': 'Motorista marcado como concluído.', 'completed': saved})

@app.route('/api/concluidos', methods=['GET'])
def get_concluidos():
    concluidos = fetch_concluidos_by_date()
    return jsonify(concluidos)


@app.route('/api/concluidos/limpar', methods=['POST'])
def limpar_concluidos():
    payload = request.get_json(silent=True) or {}
    if not clear_concluidos(payload.get('password', '')):
        return jsonify({'success': False, 'message': 'Senha inválida.'}), 401
    return jsonify({'success': True, 'message': 'Concluídos limpos com sucesso.'})


@app.route('/api/vagas', methods=['GET'])
def get_vagas():
    return jsonify(fetch_vagas_assignments())


@app.route('/api/vagas', methods=['POST'])
def save_vaga():
    payload = request.get_json(silent=True) or {}
    vaga_index = payload.get('vaga_index')
    item = payload.get('item') or {}

    if vaga_index is None:
        return jsonify({'success': False, 'message': 'Informe a vaga.'}), 400

    saved = save_vaga_assignment(vaga_index, item)
    return jsonify({'success': True, 'vaga': saved})


@app.route('/api/vagas/remover', methods=['POST'])
def remove_vaga():
    payload = request.get_json(silent=True) or {}
    vaga_index = payload.get('vaga_index')
    lt = payload.get('lt')

    if vaga_index is None and not lt:
        return jsonify({'success': False, 'message': 'Informe a vaga ou a LT.'}), 400

    removed = remove_vaga_assignment(vaga_index=vaga_index, lt=lt)
    return jsonify({'success': True, 'removed': removed, 'vaga_index': int(vaga_index) if vaga_index is not None else None})


@app.route('/api/carregamento', methods=['GET'])
def get_carregamento():
    carregamento_file = get_data_path('carregamento.json')
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
        dados = extrair_dados_filtrados(tmp_path)
        save_data(get_data_path('descarregamento.json'), dados)
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Erro ao processar CSV: {exc}'}), 500

    return jsonify({'success': True, 'message': 'Dados extraídos e salvos no JSON.', 'count': len(dados), 'data': dados})

@app.route('/api/limpar-descarregamento', methods=['POST'])
def limpar_descarregamento():
    try:
        save_data(get_data_path('descarregamento.json'), [])
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