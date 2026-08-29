import json
import os
import tempfile
from pathlib import Path


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / 'data'


def get_data_dir() -> Path:
    env_dir = os.getenv('APP_DATA_DIR')
    candidates = []

    if env_dir:
        candidates.append(Path(env_dir).expanduser())

    candidates.extend([
        DEFAULT_DATA_DIR,
        Path(tempfile.gettempdir()) / 'api_trabalho_data',
    ])

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            if os.access(candidate, os.W_OK):
                return candidate
        except OSError:
            continue

    return DEFAULT_DATA_DIR


def get_data_path(filename: str) -> Path:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / filename


def load_data(data_file: Path):
    path = Path(data_file)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(data_file: Path, data):
    path = Path(data_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')