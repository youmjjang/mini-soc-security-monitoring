import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

def load_json_list(filename):
    path = BASE_DIR / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_json_list(filename, items):
    (BASE_DIR / filename).write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def append_json(filename, item):
    items = load_json_list(filename)
    items.append(item)
    save_json_list(filename, items)

def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")
