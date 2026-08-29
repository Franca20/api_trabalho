from __future__ import annotations

import hmac
import os
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.utils import get_data_path, load_data, save_data

CONCLUIDOS_FILE = get_data_path('d_concluidos.json')
PARANA_TIMEZONE = ZoneInfo('America/Sao_Paulo')


def _normalize_lt(item: dict[str, Any]) -> str:
    return str(item.get('LT') or item.get('lt') or '').strip()


def _normalize_plate_value(item: dict[str, Any]) -> str:
    plates = item.get('Vehicle Plate Number') or item.get('vehicle_plate_number') or item.get('plates')
    if isinstance(plates, list):
        plates = ','.join(str(p).strip() for p in plates if p)
    return str(plates or '-').strip()


def _normalize_station_value(item: dict[str, Any]) -> str:
    return str(item.get('Station Name') or item.get('station_name') or item.get('station') or '-').strip()


def _normalize_schedule_value(item: dict[str, Any]) -> str:
    return str(
        item.get('Schedule Arrival Time')
        or item.get('schedule_arrival_time')
        or item.get('schedule')
        or item.get('ETA')
        or '-'
    ).strip()


def _normalize_to_value(item: dict[str, Any]) -> str:
    return str(item.get('TO') or item.get('to_value') or item.get('to') or '-').strip()


def save_concluded(item: dict[str, Any], concluded_at: datetime | None = None) -> dict[str, Any]:
    lt = _normalize_lt(item)
    if not lt:
        raise ValueError('LT inválida para registro de concluído.')

    concluded_at = concluded_at or datetime.now(PARANA_TIMEZONE)
    record = {
        'LT': lt,
        'lt': lt,
        'Station Name': _normalize_station_value(item),
        'station_name': _normalize_station_value(item),
        'Vehicle Plate Number': _normalize_plate_value(item),
        'vehicle_plate_number': _normalize_plate_value(item),
        'Driver': str(item.get('Driver') or item.get('driver') or '-').strip(),
        'driver': str(item.get('Driver') or item.get('driver') or '-').strip(),
        'Schedule Arrival Time': _normalize_schedule_value(item),
        'schedule_arrival_time': _normalize_schedule_value(item),
        'TO': _normalize_to_value(item),
        'to_value': _normalize_to_value(item),
        'status': str(item.get('status') or 'concluido').strip(),
        'concluido_em': concluded_at.strftime('%d/%m/%Y %H:%M:%S'),
    }

    records = load_data(CONCLUIDOS_FILE)
    if not isinstance(records, list):
        records = []

    records = [existing for existing in records if str(existing.get('LT') or existing.get('lt') or '').strip() != lt]
    records.append(record)
    save_data(CONCLUIDOS_FILE, records)

    plates = [plate.strip() for plate in str(record['Vehicle Plate Number']).split(',') if plate.strip()]
    if not plates:
        plates = [record['Vehicle Plate Number'] or '-']

    return {
        'LT': lt,
        'driver': record['Driver'],
        'plates': plates,
        'schedule': record['Schedule Arrival Time'],
        'status': record['status'],
        'concluido_em': concluded_at.strftime('%d/%m/%Y %H:%M:%S'),
    }


def fetch_concluidos_by_date(target_date: date | None = None) -> list[dict[str, Any]]:
    records = load_data(CONCLUIDOS_FILE)
    if not isinstance(records, list):
        return []

    normalized_records: list[dict[str, Any]] = []
    for record in records:
        plates_value = record.get('vehicle_plate_number') or record.get('Vehicle Plate Number') or record.get('plates') or ''
        plates = plates_value if isinstance(plates_value, list) else str(plates_value).split(',')
        plates = [plate.strip() for plate in plates if str(plate).strip()]
        if not plates:
            plates = ['-']
        normalized_records.append(
            {
                'LT': str(record.get('LT') or record.get('lt') or '-'),
                'driver': str(record.get('driver') or record.get('Driver') or '-'),
                'plates': plates,
                'schedule': str(record.get('schedule_arrival_time') or record.get('Schedule Arrival Time') or record.get('schedule') or '-'),
                'status': str(record.get('status') or 'concluido'),
                'concluido_em': str(record.get('concluido_em') or '-'),
            }
        )
    return normalized_records


def is_concluded(lt: str, target_date: date | None = None) -> bool:
    if not lt:
        return False
    normalized_lt = str(lt).strip()
    return any(item.get('LT') == normalized_lt for item in fetch_concluidos_by_date())


def clear_concluidos(password: str) -> bool:
    expected_password = os.getenv('LIMPAR_CONCLUIDOS_SENHA', '')
    if not expected_password or not hmac.compare_digest(str(password), expected_password):
        return False
    save_data(CONCLUIDOS_FILE, [])
    return True
