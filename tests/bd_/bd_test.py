from __future__ import annotations

from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    create_engine,
    text,
)

from extrair_descarregamento import extrair_dados_filtrados

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.")
TABLE_NAME = "descarregamento"


def create_table(engine):
    metadata = MetaData()
    table = Table(
        TABLE_NAME,
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
    metadata.create_all(engine)
    return table


def build_records(csv_path: Path) -> list[dict[str, str]]:
    extracted = extrair_dados_filtrados(csv_path)
    return [
        {
            "lt": item.get("LT", "-"),
            "station_name": item.get("Station Name", "-"),
            "vehicle_plate_number": item.get("Vehicle Plate Number", "-"),
            "driver": item.get("Driver", "-"),
            "schedule_arrival_time": item.get("Schedule Arrival Time", "-"),
            "to_value": item.get("TO", "-"),
        }
        for item in extracted
    ]


def main() -> None:
    engine = create_engine(DATABASE_URL)
    table = create_table(engine)
    csv_path = Path(__file__).resolve().parent / "descarregamento.csv"
    records = build_records(csv_path)

    if not records:
        print("Nenhum registro extraído. Verifique o CSV e o extractor.")
        return

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY"))
        result = conn.execute(table.insert(), records)
        print(f"Inseridos {result.rowcount} registros na tabela '{TABLE_NAME}'.")


if __name__ == "__main__":
    main()
