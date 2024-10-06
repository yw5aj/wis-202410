import json
from pathlib import Path

GROUP_DATA_DIR = Path("group_data")
GROUP_DATA_DIR.mkdir(exist_ok=True)

def save_group_data(group_name, data_type, content):
    file_path = GROUP_DATA_DIR / f"{group_name}_{data_type}.json"
    with open(file_path, "w") as f:
        json.dump(content, f)

def load_group_data(group_name, data_type):
    file_path = GROUP_DATA_DIR / f"{group_name}_{data_type}.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            return json.load(f)
    return None