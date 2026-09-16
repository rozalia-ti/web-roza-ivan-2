import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data.json"


def load_students():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(students, file, ensure_ascii=False, indent=2)
