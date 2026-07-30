from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, select, text
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


def fetch_descarregamento_data() -> list[dict[str, Any]]:
    try:
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
