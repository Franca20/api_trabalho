from __future__ import annotations

from pathlib import Path
import os
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
    select,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.")

engine: Engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

descarregamento_table = Table(
    "descarregamento",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("lt", String(128), nullable=False),
    Column("station_name", String(255)),
    Column("vehicle_plate_number", String(255)),
    Column("driver", String(255)),
    Column("schedule_arrival_time", String(128)),
    Column("to_value", String(128)),
    Column("created_at", DateTime, server_default=text("NOW()")),
)


def create_tables() -> None:
    try:
        metadata.create_all(engine)
    except SQLAlchemyError as exc:
        print(f"[DB] Erro ao criar tabela: {exc}")


def fetch_descarregamento_data() -> list[dict[str, str]]:
    try:
        create_tables()
        with engine.connect() as conn:
            result = conn.execute(select(descarregamento_table))
            rows = result.fetchall()
    except SQLAlchemyError as exc:
        print(f"[DB] Erro ao buscar dados: {exc}")
        return []

    return [
        {
            "LT": str(row["lt"] or "-"),
            "Station Name": str(row["station_name"] or "-"),
            "Vehicle Plate Number": str(row["vehicle_plate_number"] or "-"),
            "Driver": str(row["driver"] or "-"),
            "Schedule Arrival Time": str(row["schedule_arrival_time"] or "-"),
            "TO": str(row["to_value"] or "-"),
        }
        for row in rows
    ]


def save_descarregamento_data(records: list[dict[str, Any]]) -> None:
    try:
        create_tables()
        with engine.begin() as conn:
            conn.execute(descarregamento_table.delete())
            if records:
                conn.execute(descarregamento_table.insert(), records)
    except SQLAlchemyError as exc:
        print(f"[DB] Erro ao salvar dados: {exc}")
        raise
