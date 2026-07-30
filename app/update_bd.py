from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import json


base = Path(__file__).parent
def update_database():
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.")
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM descarregamento;"))
            dados = []
            for row in result:
                id, lt, station_name, vehicle_plate_number, driver, schedule_arrival_time, to_value, created_at = row
                driver_data = {
                    "LT": lt,
                    "Station Name": station_name,
                    "Vehicle Plate Number": vehicle_plate_number,
                    "Driver": driver,
                    "Schedule Arrival Time": schedule_arrival_time,
                    "TO": to_value
                }
                dados.append(driver_data)

        with open(base / "data/descarregamento.json", "w") as f:
            data = json.dumps(dados, indent=4)
            f.write(data)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados ou buscar dados: {e}")
try:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não encontrado. Defina-o no arquivo .env ou nas variáveis de ambiente.")
    engine = create_engine(DATABASE_URL)
    dados = []
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM descarregamento;"))
        for row in result:
            id, lt, station_name, vehicle_plate_number, driver, schedule_arrival_time, to_value, created_at = row
            driver = {
                        "LT": lt,
                        "Station Name": station_name,
                        "Vehicle Plate Number": vehicle_plate_number,
                        "Driver": driver,
                        "Schedule Arrival Time": schedule_arrival_time,
                        "TO": to_value
                    }
            dados.append(driver)

    with open(base / "data/descarregamento.json", "w") as f:
        data = json.dumps(dados, indent=4)
        f.write(data)
except Exception as e:
    print(f"Erro ao conectar ao banco de dados ou buscar dados: {e}")