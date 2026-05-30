import json
from pathlib import Path

base_dir = Path(__file__).parent
data_file = base_dir / 'dados.json'

def load_data():
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        return []
    
if __name__ == "__main__":
    data = load_data()
    print(data)