from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.engine import Engine

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.')

engine: Engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

descarregamento = Table(
    'descarregamento',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('lt', String(128), nullable=False),
    Column('station_name', String(255)),
    Column('vehicle_plate_number', String(255)),
    Column('driver', String(255)),
    Column('schedule_arrival_time', String(128)),
    Column('to_value', String(128)),
    Column('created_at', DateTime, server_default=text('NOW()')),
)

vagas = Table(
    'vagas',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('vaga_index', Integer, nullable=False, unique=True),
    Column('lt', String(128)),
    Column('driver', String(255)),
    Column('station_name', String(255)),
    Column('vehicle_plate_number', String(255)),
    Column('schedule_arrival_time', String(128)),
    Column('to_value', String(128)),
    Column('plates', String(255)),
    Column('created_at', DateTime, server_default=text('NOW()')),
)


def create_tables() -> None:
    metadata.create_all(engine)


def _clean_plate_value(value: Any) -> str:
    if isinstance(value, list):
        return ','.join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ''
    return str(value).strip()


def fetch_descarregamento_data() -> list[dict[str, Any]]:
    try:
        create_tables()
        with engine.connect() as conn:
            result = conn.execute(select(descarregamento))
            rows = result.fetchall()
    except Exception as exc:
        print(f'[DB] Erro ao buscar dados de descarregamento: {exc}')
        return []

    return [
        {
            'LT': row.lt or '',
            'Station Name': row.station_name or '',
            'Vehicle Plate Number': row.vehicle_plate_number or '',
            'Driver': row.driver or '',
            'Schedule Arrival Time': row.schedule_arrival_time or '',
            'TO': row.to_value or '',
        }
        for row in rows
    ]


def fetch_vagas_assignments() -> list[dict[str, Any]]:
    try:
        create_tables()
        with engine.connect() as conn:
            result = conn.execute(select(vagas).order_by(vagas.c.vaga_index.asc()))
            rows = result.fetchall()
    except Exception as exc:
        print(f'[DB] Erro ao buscar vagas: {exc}')
        return []

    records: list[dict[str, Any]] = []
    for row in rows:
        plates_value = row.plates or row.vehicle_plate_number or ''
        plates = [plate.strip() for plate in str(plates_value).split(',') if plate.strip()]
        if not plates and row.vehicle_plate_number:
            plates = [row.vehicle_plate_number]

        records.append({
            'vaga_index': row.vaga_index,
            'lt': row.lt or '',
            'LT': row.lt or '',
            'driver': row.driver or '',
            'Driver': row.driver or '',
            'station': row.station_name or '',
            'Station Name': row.station_name or '',
            'schedule': row.schedule_arrival_time or '',
            'Schedule Arrival Time': row.schedule_arrival_time or '',
            'to': row.to_value or '',
            'TO': row.to_value or '',
            'plates': plates,
            'Vehicle Plate Number': row.vehicle_plate_number or '',
            'platesString': ', '.join(plates),
        })
    return records


def save_vaga_assignment(vaga_index: int, item: dict[str, Any]) -> dict[str, Any]:
    create_tables()
    vaga_number = int(vaga_index)
    record = {
        'vaga_index': vaga_number,
        'lt': str(item.get('LT') or item.get('lt') or '').strip(),
        'driver': str(item.get('Driver') or item.get('driver') or '').strip(),
        'station_name': str(item.get('Station Name') or item.get('station_name') or item.get('station') or '').strip(),
        'vehicle_plate_number': _clean_plate_value(item.get('Vehicle Plate Number') or item.get('vehicle_plate_number') or item.get('plates')),
        'schedule_arrival_time': str(item.get('Schedule Arrival Time') or item.get('schedule_arrival_time') or item.get('schedule') or '').strip(),
        'to_value': str(item.get('TO') or item.get('to_value') or item.get('to') or '').strip(),
        'plates': _clean_plate_value(item.get('plates') or item.get('Vehicle Plate Number') or item.get('vehicle_plate_number')),
    }

    with engine.begin() as conn:
        existing = conn.execute(select(vagas.c.id).where(vagas.c.vaga_index == vaga_number)).first()
        if existing:
            conn.execute(update(vagas).where(vagas.c.vaga_index == vaga_number).values(**record))
        else:
            conn.execute(insert(vagas).values(**record))

    plates = [plate.strip() for plate in record['plates'].split(',') if plate.strip()]
    if not plates and record['vehicle_plate_number']:
        plates = [record['vehicle_plate_number']]

    return {
        'vaga_index': vaga_number,
        'lt': record['lt'],
        'driver': record['driver'],
        'station': record['station_name'],
        'schedule': record['schedule_arrival_time'],
        'to': record['to_value'],
        'plates': plates,
        'Vehicle Plate Number': record['vehicle_plate_number'],
        'platesString': record['plates'] or record['vehicle_plate_number'],
    }


def remove_vaga_assignment(vaga_index: int | None = None, lt: str | None = None) -> bool:
    create_tables()
    if vaga_index is None and not lt:
        return False

    try:
        with engine.begin() as conn:
            if vaga_index is not None:
                result = conn.execute(delete(vagas).where(vagas.c.vaga_index == int(vaga_index)))
            elif lt is not None:
                result = conn.execute(delete(vagas).where(vagas.c.lt == str(lt).strip()))
            else:
                result = None
        return bool(result and getattr(result, 'rowcount', 0) > 0)
    except Exception as exc:
        print(f'[DB] Erro ao remover vaga: {exc}')
        return False
