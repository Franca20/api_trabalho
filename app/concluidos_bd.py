from __future__ import annotations

import os
import hmac
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy import (
    and_,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    select,
    text,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.utils import load_data, save_data

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.")

engine: Engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()
CONCLUIDOS_FILE = Path(__file__).parent / 'data' / 'd_concluidos.json'
PARANA_TIMEZONE = ZoneInfo('America/Sao_Paulo')

motoristas_concluidos = Table(
    "motoristas_concluidos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("lt", String(128), nullable=False),
    Column("station_name", String(255)),
    Column("vehicle_plate_number", String(255)),
    Column("driver", String(255)),
    Column("schedule_arrival_time", String(128)),
    Column("to_value", String(128)),
    Column("status", String(64), nullable=False, server_default=text("'concluido'")),
    Column("concluded_at", DateTime(timezone=True), nullable=False),
    Column("concluded_date", Date, nullable=False),
)


def create_tables() -> None:
    try:
        metadata.create_all(engine)
    except SQLAlchemyError as exc:
        print(f"[CONCLUIDOS_DB] Erro ao criar tabela: {exc}")


def _normalize_lt(item: dict[str, Any]) -> str:
    return str(item.get("LT") or item.get("lt") or "").strip()


def _cleanup_old_records(current_date: date | None = None) -> None:
    create_tables()
    if current_date is None:
        current_date = datetime.now(PARANA_TIMEZONE).date()
    try:
        with engine.begin() as conn:
            conn.execute(
                motoristas_concluidos.delete().where(
                    motoristas_concluidos.c.concluded_date != current_date
                )
            )
    except SQLAlchemyError as exc:
        print(f"[CONCLUIDOS_DB] Erro ao limpar registros antigos: {exc}")


def _normalize_plate_value(item: dict[str, Any]) -> str:
    plates = item.get("Vehicle Plate Number") or item.get("vehicle_plate_number") or item.get("plates")
    if isinstance(plates, list):
        plates = ",".join(str(p).strip() for p in plates if p)
    return str(plates or "-").strip()


def _normalize_station_value(item: dict[str, Any]) -> str:
    return str(item.get("Station Name") or item.get("station_name") or item.get("station") or "-").strip()


def _normalize_schedule_value(item: dict[str, Any]) -> str:
    return str(
        item.get("Schedule Arrival Time")
        or item.get("schedule_arrival_time")
        or item.get("schedule")
        or item.get("ETA")
        or "-"
    ).strip()


def _normalize_to_value(item: dict[str, Any]) -> str:
    return str(item.get("TO") or item.get("to_value") or item.get("to") or "-").strip()


def save_concluded(item: dict[str, Any], concluded_at: datetime | None = None) -> dict[str, Any]:
    lt = _normalize_lt(item)
    if not lt:
        raise ValueError("LT inválida para registro de concluído.")

    concluded_at = concluded_at or datetime.now(PARANA_TIMEZONE)
    record = {
        "lt": lt,
        "station_name": _normalize_station_value(item),
        "vehicle_plate_number": _normalize_plate_value(item),
        "driver": str(item.get("Driver") or item.get("driver") or "-").strip(),
        "schedule_arrival_time": _normalize_schedule_value(item),
        "to_value": _normalize_to_value(item),
        "status": str(item.get("status") or "concluido").strip(),
        "concluido_em": concluded_at.strftime('%d/%m/%Y %H:%M:%S'),
    }

    records = load_data(CONCLUIDOS_FILE)
    if not isinstance(records, list):
        records = []
    records = [existing for existing in records if str(existing.get('LT') or existing.get('lt') or '').strip() != lt]
    records.append(record)
    save_data(CONCLUIDOS_FILE, records)

    plates = [plate.strip() for plate in record["vehicle_plate_number"].split(",") if plate.strip()]
    if not plates:
        plates = [record["vehicle_plate_number"] or "-"]

    return {
        "LT": lt,
        "driver": record["driver"],
        "plates": plates,
        "schedule": record["schedule_arrival_time"],
        "status": record["status"],
        "concluido_em": concluded_at.strftime('%d/%m/%Y %H:%M:%S'),
    }


def fetch_concluidos_by_date(target_date: date | None = None) -> list[dict[str, Any]]:
    records = load_data(CONCLUIDOS_FILE)
    if not isinstance(records, list):
        return []

    normalized_records: list[dict[str, Any]] = []
    for record in records:
        plates_value = record.get('vehicle_plate_number') or record.get('plates') or ''
        plates = plates_value if isinstance(plates_value, list) else str(plates_value).split(',')
        plates = [plate.strip() for plate in plates if str(plate).strip()]
        if not plates:
            plates = ["-"]
        normalized_records.append(
            {
                "LT": str(record.get('LT') or record.get('lt') or "-"),
                "driver": str(record.get('driver') or record.get('Driver') or "-"),
                "plates": plates,
                "schedule": str(record.get('schedule_arrival_time') or record.get('schedule') or "-"),
                "status": str(record.get('status') or "concluido"),
                "concluido_em": str(record.get('concluido_em') or "-"),
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
