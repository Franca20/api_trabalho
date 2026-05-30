import json
from pathlib import Path

def load_data(data_file: Path):
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        return []