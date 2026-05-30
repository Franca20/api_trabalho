"""
Extração de dados de CSV com filtro em Inbound(TO).

Campos desejados:
- LH Trip Number
- Station Name
- Vehicle Plate Number
- Driver
- Schedule Arrival Time

Regra de filtro:
- A linha só entra no resultado quando Inbound(TO) for diferente de "0/0".
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path


COLUNAS_DESEJADAS = {
	"lh_trip_number": "LH Trip Number",
	"station_name": "Station Name",
	"station_number": "Station Number",
	"vehicle_plate_number": "Vehicle Plate Number",
	"driver": "Driver",
	"schedule_arrival_time": "Schedule Arrival Time",
	"inbound_to": "Inbound(TO)",
}

ALIAS_COLUNAS = {
		"station_number": [
			"station number",
			"stationnumber",
			"número estação",
			"numero estacao",
			"num estacao",
			"num estação",
		],
	"lh_trip_number": [
		"lh trip number",
		"trip number",
		"trip",
		"lt",
		"numero viagem",
		"número viagem",
	],
	"station_name": [
		"station name",
		"station",
		"destino",
		"nome estacao",
		"nome estação",
	],
	"vehicle_plate_number": [
		"vehicle plate number",
		"vehicle plate",
		"plate number",
		"plate",
		"placa",
		"placa do veiculo",
		"placa do veículo",
	],
	"driver": [
		"driver",
		"motorista",
		"nome motorista",
	],
	"schedule_arrival_time": [
		"schedule arrival time",
		"arrival time",
		"eta",
		"horario chegada",
		"horário chegada",
	],
	"inbound_to": [
		"inbound(to)",
		"inbound to",
		"inbound",
		"to",
		"tos",
	],
}


def _normalizar_cabecalho(nome: str) -> str:
	return " ".join((nome or "").strip().lower().split())


def _valor_normalizado(valor: str) -> str:
	return (valor or "").strip().replace(" ", "")


def _normalizar_chave_flexivel(texto: str) -> str:
	base = _normalizar_cabecalho(texto)
	return ''.join(ch for ch in base if ch.isalnum())


def _resolver_coluna(mapa_cabecalhos: dict[str, str], campo: str) -> str | None:
	"""Resolve coluna por nome esperado, aliases e aproximação textual."""
	chaves_esperadas = [COLUNAS_DESEJADAS.get(campo, "")] + ALIAS_COLUNAS.get(campo, [])
	normalizadas = [_normalizar_cabecalho(item) for item in chaves_esperadas if item]

	# 1) Match exato normalizado
	for chave in normalizadas:
		coluna = mapa_cabecalhos.get(chave)
		if coluna:
			return coluna

	# 2) Match flexível (remove símbolos/espaços)
	mapa_flexivel = {_normalizar_chave_flexivel(k): v for k, v in mapa_cabecalhos.items()}
	for chave in normalizadas:
		alvo = _normalizar_chave_flexivel(chave)
		if not alvo:
			continue
		if alvo in mapa_flexivel:
			return mapa_flexivel[alvo]

	# 3) Contém / contido (fallback)
	for chave in normalizadas:
		alvo = _normalizar_chave_flexivel(chave)
		if not alvo:
			continue
		for cabecalho_norm, coluna_original in mapa_cabecalhos.items():
			cab_flex = _normalizar_chave_flexivel(cabecalho_norm)
			if alvo and cab_flex and (alvo in cab_flex or cab_flex in alvo):
				return coluna_original

	return None


def _obter_valor_coluna(linha: dict[str, str], coluna: str | None, padrao: str = "-") -> str:
	if not coluna:
		return padrao
	valor = (linha.get(coluna) or "").strip()
	return valor if valor else padrao


def _normalizar_to(valor_inbound: str) -> str:
	"""Retorna apenas o valor à direita da barra em TO.

	Exemplos:
	- '0/26' -> '26'
	- '0/78' -> '78'
	- '26' -> '26'
	"""
	texto = (valor_inbound or "").strip()
	if not texto:
		return "-"

	texto_sem_espaco = texto.replace(" ", "")
	if "/" in texto_sem_espaco:
		parte_direita = texto_sem_espaco.split("/")[-1].strip()
		return parte_direita or "-"

	return texto_sem_espaco


def _ler_linhas_filtradas(texto_csv: str) -> list[dict[str, str]]:
	amostra = (texto_csv or "")[:4096]
	try:
		dialeto = csv.Sniffer().sniff(amostra, delimiters=",;")
	except csv.Error:
		dialeto = csv.excel

	leitor = csv.DictReader(StringIO(texto_csv), dialect=dialeto)

	cabecalhos = leitor.fieldnames or []
	mapa_cabecalhos = {_normalizar_cabecalho(c): c for c in cabecalhos}

	coluna_lh = _resolver_coluna(mapa_cabecalhos, "lh_trip_number")
	coluna_station = _resolver_coluna(mapa_cabecalhos, "station_name")
	coluna_plate = _resolver_coluna(mapa_cabecalhos, "vehicle_plate_number")
	coluna_driver = _resolver_coluna(mapa_cabecalhos, "driver")
	coluna_arrival = _resolver_coluna(mapa_cabecalhos, "schedule_arrival_time")
	coluna_inbound = _resolver_coluna(mapa_cabecalhos, "inbound_to")

	# Inbound(TO) é a única coluna realmente obrigatória para aplicar o filtro.
	# Se não existir, retorna vazio sem quebrar o site em produção.
	if coluna_inbound is None:
		return []

	coluna_station_number = _resolver_coluna(mapa_cabecalhos, "station_number")
	if not coluna_station_number:
		print("[ERRO] Coluna 'Station Number' não encontrada no CSV.")
		return []

	lt_dict = {}
	linhas_station2 = []
	for linha in leitor:
		station_number_val = _obter_valor_coluna(linha, coluna_station_number)
		inbound_valor = _obter_valor_coluna(linha, coluna_inbound)
		lt = _obter_valor_coluna(linha, coluna_lh)
		try:
			station_number_int = int(str(station_number_val).strip())
		except Exception:
			print(f"[DEBUG] Linha ignorada: Station Number inválido: {station_number_val} | inbound(TO): {inbound_valor} | LT: {lt}")
			continue
		print(f"[DEBUG] Station Number: {station_number_int} | inbound(TO): {inbound_valor} | LT: {lt}")
		if station_number_int == 1:
			lt_dict[lt] = {
				"LT": lt,
				"Station Name": _obter_valor_coluna(linha, coluna_station),
				"Vehicle Plate Number": "-",
				"Driver": "-",
				"Schedule Arrival Time": "-",
				"TO": "-"
			}
		elif station_number_int == 2:
			linhas_station2.append(linha)

	for linha in linhas_station2:
		lt = _obter_valor_coluna(linha, coluna_lh)
		if lt in lt_dict:
			inbound_valor = _obter_valor_coluna(linha, coluna_inbound)
			to_valor = _normalizar_to(inbound_valor)
			lt_dict[lt].update({
				"Vehicle Plate Number": _obter_valor_coluna(linha, coluna_plate),
				"Driver": _obter_valor_coluna(linha, coluna_driver),
				"Schedule Arrival Time": _obter_valor_coluna(linha, coluna_arrival),
				"TO": to_valor
			})

	return list(lt_dict.values())


def extrair_dados_filtrados_conteudo(texto_csv: str) -> list[dict[str, str]]:
	return _ler_linhas_filtradas(texto_csv)


def extrair_dados_filtrados(caminho_csv: str | Path) -> list[dict[str, str]]:
	caminho_csv = Path(caminho_csv)
	texto_csv = caminho_csv.read_text(encoding="utf-8-sig")
	return _ler_linhas_filtradas(texto_csv)


if __name__ == "__main__":
	from pathlib import Path
	import json
	base = Path(__file__).parent

	arquivo_csv = Path(base / 'data.csv')
	dados = extrair_dados_filtrados(arquivo_csv)

	try:
		with open(base / 'dados.json', 'w') as file:
			data = json.dumps(dados, indent=4)
			file.write(data)
	except:
		print('erro')