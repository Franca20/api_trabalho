"""Campos esperados no CSV (exatamente como no arquivo):
LH Trip Number,
Station Number,
Station Name,
Vehicle Plate Number,
Driver,
Schedule Arrival Time,
Actual Arrival Time,
CPT Type,

Extrai `tests/carregamento/dados_carregamento.csv` para JSON.

Uso:
  python tests/carregamento/extrair_carregamento.py --station 1

Também pode ser importado e usado programaticamente via `csv_to_json()`.
"""

from pathlib import Path
import csv
import json
import argparse

SELECTED_FIELDS = [
    "LH Trip Number",
    "Station Number",
    "Station Name",
    "Vehicle Plate Number",
    "Driver",
    "Schedule Arrival Time",
    # "Actual Arrival Time",
    # "CPT Type",
]


def csv_to_json(input_path, output_path, station_number=None, encoding="utf-8-sig", fields=None):
	input_path = Path(input_path)
	output_path = Path(output_path)
	if not input_path.exists():
		raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

	if fields is None:
		fields = SELECTED_FIELDS

	with input_path.open("r", encoding=encoding, newline="") as f:
		reader = csv.DictReader(f)
		rows = []
		desired = None if station_number is None else str(station_number).strip()
		for row in reader:
			if desired is not None and (row.get("Station Number") or "").strip() != desired:
				continue
			filtered = {field: (row.get(field) or "").strip() for field in fields}
			rows.append(filtered)

	with output_path.open("w", encoding="utf-8") as f:
		json.dump(rows, f, ensure_ascii=False, indent=2)

	return output_path


def main():
	default_input = Path(__file__).parent / "carregamento.csv"
	default_output = Path(__file__).parent / "carregamento.json"

	parser = argparse.ArgumentParser(description="Converter CSV de carregamento para JSON")
	parser.add_argument("--input", "-i", default=str(default_input), help="Caminho do CSV de entrada")
	parser.add_argument("--output", "-o", default=str(default_output), help="Caminho do JSON de saída")
	parser.add_argument("--station", "-s", default="1", help="Filtrar por Station Number (padrão: 1)")
	args = parser.parse_args()

	out = csv_to_json(args.input, args.output, station_number=args.station)
	print(f"Gerado: {out}")


if __name__ == "__main__":
	main()


