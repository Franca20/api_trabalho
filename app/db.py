from __future__ import annotations

from typing import Any

from app.utils import get_data_path, load_data, save_data

VAGAS_FILE = get_data_path('vagas.json')


def _normalize_plates(value: Any) -> list[str]:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
    elif value is None:
        parts = []
    else:
        parts = [part.strip() for part in str(value).split(',') if part.strip()]
    return parts


def _clean_plate_value(value: Any) -> str:
    return ','.join(_normalize_plates(value))


def fetch_descarregamento_data() -> list[dict[str, Any]]:
    return load_data(get_data_path('descarregamento.json'))


def fetch_vagas_assignments() -> list[dict[str, Any]]:
    records = load_data(VAGAS_FILE)
    if not isinstance(records, list):
        return []

    normalized: list[dict[str, Any]] = []
    for record in records:
        plates = _normalize_plates(record.get('plates') or record.get('Vehicle Plate Number') or record.get('vehicle_plate_number'))
        if not plates and record.get('Vehicle Plate Number'):
            plates = _normalize_plates(record.get('Vehicle Plate Number'))

        normalized.append({
            'vaga_index': int(record.get('vaga_index') or 0),
            'lt': str(record.get('lt') or record.get('LT') or '').strip(),
            'LT': str(record.get('LT') or record.get('lt') or '').strip(),
            'driver': str(record.get('driver') or record.get('Driver') or '').strip(),
            'Driver': str(record.get('Driver') or record.get('driver') or '').strip(),
            'station': str(record.get('station') or record.get('Station Name') or '').strip(),
            'Station Name': str(record.get('Station Name') or record.get('station') or '').strip(),
            'schedule': str(record.get('schedule') or record.get('Schedule Arrival Time') or '').strip(),
            'Schedule Arrival Time': str(record.get('Schedule Arrival Time') or record.get('schedule') or '').strip(),
            'to': str(record.get('to') or record.get('TO') or '').strip(),
            'TO': str(record.get('TO') or record.get('to') or '').strip(),
            'plates': plates,
            'Vehicle Plate Number': ', '.join(plates),
            'platesString': ', '.join(plates),
        })

    return sorted(normalized, key=lambda item: int(item.get('vaga_index') or 0))


def save_vaga_assignment(vaga_index: int, item: dict[str, Any]) -> dict[str, Any]:
    vaga_number = int(vaga_index)
    record = {
        'vaga_index': vaga_number,
        'lt': str(item.get('LT') or item.get('lt') or '').strip(),
        'LT': str(item.get('LT') or item.get('lt') or '').strip(),
        'driver': str(item.get('Driver') or item.get('driver') or '').strip(),
        'Driver': str(item.get('Driver') or item.get('driver') or '').strip(),
        'station': str(item.get('Station Name') or item.get('station_name') or item.get('station') or '').strip(),
        'Station Name': str(item.get('Station Name') or item.get('station_name') or item.get('station') or '').strip(),
        'schedule': str(item.get('Schedule Arrival Time') or item.get('schedule_arrival_time') or item.get('schedule') or '').strip(),
        'Schedule Arrival Time': str(item.get('Schedule Arrival Time') or item.get('schedule_arrival_time') or item.get('schedule') or '').strip(),
        'to': str(item.get('TO') or item.get('to_value') or item.get('to') or '').strip(),
        'TO': str(item.get('TO') or item.get('to_value') or item.get('to') or '').strip(),
        'plates': _normalize_plates(item.get('plates') or item.get('Vehicle Plate Number') or item.get('vehicle_plate_number')),
        'Vehicle Plate Number': _clean_plate_value(item.get('Vehicle Plate Number') or item.get('vehicle_plate_number') or item.get('plates')),
    }

    records = load_data(VAGAS_FILE)
    if not isinstance(records, list):
        records = []

    existing_index = next((idx for idx, existing in enumerate(records) if int(existing.get('vaga_index') or 0) == vaga_number), None)
    if existing_index is not None:
        records[existing_index] = record
    else:
        records.append(record)

    save_data(VAGAS_FILE, records)

    plates = record['plates']
    return {
        'vaga_index': vaga_number,
        'lt': record['lt'],
        'driver': record['driver'],
        'station': record['station'],
        'schedule': record['schedule'],
        'to': record['to'],
        'plates': plates,
        'Vehicle Plate Number': record['Vehicle Plate Number'],
        'platesString': ', '.join(plates),
    }


def remove_vaga_assignment(vaga_index: int | None = None, lt: str | None = None) -> bool:
    if vaga_index is None and not lt:
        return False

    records = load_data(VAGAS_FILE)
    if not isinstance(records, list):
        return False

    filtered = []
    removed = False
    for record in records:
        current_vaga = record.get('vaga_index')
        current_lt = str(record.get('lt') or record.get('LT') or '').strip()
        if vaga_index is not None and current_vaga == int(vaga_index):
            removed = True
            continue
        if lt is not None and current_lt == str(lt).strip():
            removed = True
            continue
        filtered.append(record)

    if removed:
        save_data(VAGAS_FILE, filtered)

    return removed
