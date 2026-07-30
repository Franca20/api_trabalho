from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

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

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.")

engine: Engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

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
    current_date = current_date or date.today()
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
    create_tables()
    lt = _normalize_lt(item)
    if not lt:
        raise ValueError("LT inválida para registro de concluído.")

    concluded_at = concluded_at or datetime.now()
    concluded_date = concluded_at.date()
    _cleanup_old_records(concluded_date)

    record = {
        "lt": lt,
        "station_name": _normalize_station_value(item),
        "vehicle_plate_number": _normalize_plate_value(item),
        "driver": str(item.get("Driver") or item.get("driver") or "-").strip(),
        "schedule_arrival_time": _normalize_schedule_value(item),
        "to_value": _normalize_to_value(item),
        "status": str(item.get("status") or "concluido").strip(),
        "concluded_at": concluded_at,
        "concluded_date": concluded_date,
    }

    try:
        with engine.begin() as conn:
            existing = conn.execute(
                select(motoristas_concluidos.c.id)
                .where(
                    and_(
                        motoristas_concluidos.c.lt == lt,
                        motoristas_concluidos.c.concluded_date == concluded_date,
                    )
                )
            ).first()

            if existing:
                conn.execute(
                    update(motoristas_concluidos)
                    .where(
                        and_(
                            motoristas_concluidos.c.lt == lt,
                            motoristas_concluidos.c.concluded_date == concluded_date,
                        )
                    )
                    .values(**record)
                )
            else:
                conn.execute(motoristas_concluidos.insert().values(**record))
    except SQLAlchemyError as exc:
        raise RuntimeError(f"[CONCLUIDOS_DB] Erro ao salvar registro de concluído: {exc}")

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
    create_tables()
    target_date = target_date or date.today()
    _cleanup_old_records(target_date)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                select(motoristas_concluidos)
                .where(motoristas_concluidos.c.concluded_date == target_date)
            )
            rows = result.fetchall()
    except SQLAlchemyError as exc:
        print(f"[CONCLUIDOS_DB] Erro ao buscar registros de concluídos: {exc}")
        return []

    records: list[dict[str, Any]] = []
    for row in rows:
        plates = [plate.strip() for plate in str(row.vehicle_plate_number or "").split(",") if plate.strip()]
        if not plates:
            plates = ["-"]
        records.append(
            {
                "LT": str(row.lt or "-"),
                "driver": str(row.driver or "-"),
                "plates": plates,
                "schedule": str(row.schedule_arrival_time or "-"),
                "status": str(row.status or "concluido"),
                "concluido_em": row.concluded_at.strftime('%d/%m/%Y %H:%M:%S') if row.concluded_at else "-",
            }
        )
    return records


def is_concluded(lt: str, target_date: date | None = None) -> bool:
    if not lt:
        return False
    create_tables()
    target_date = target_date or date.today()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                select(motoristas_concluidos.c.id)
                .where(
                    and_(
                        motoristas_concluidos.c.lt == lt,
                        motoristas_concluidos.c.concluded_date == target_date,
                    )
                )
            )
            return result.first() is not None
    except SQLAlchemyError as exc:
        print(f"[CONCLUIDOS_DB] Erro ao verificar concluído: {exc}")
        return False
