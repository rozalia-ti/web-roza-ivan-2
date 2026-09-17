# Слой данных: чтение и запись студентов в JSON-файл.

import json
from pathlib import Path

# data.json в папке проекта (на два уровня выше этого файла)
DATA_FILE = Path(__file__).resolve().parent.parent / "data.json"


# Загружает всех студентов; если файла нет — пустой список.
def load_students():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# Сохраняет список в файл целиком. ensure_ascii=False — русский текст как есть.
def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(students, file, ensure_ascii=False, indent=2)
