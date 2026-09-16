# Слой работы с данными: чтение и запись списка студентов в JSON-файл.
# Другие слои (маршруты, бизнес-логика) не знают, как именно хранятся данные.

import json
from pathlib import Path

# Путь к файлу хранилища: папка проекта (на два уровня выше этого файла)
DATA_FILE = Path(__file__).resolve().parent.parent / "data.json"


# Загружает всех студентов из JSON-файла.
# Если файла ещё нет (например, при первом запуске) — возвращает пустой список.
def load_students():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# Сохраняет список студентов в JSON-файл, перезаписывая его целиком.
# ensure_ascii=False — русские буквы записываются как есть, а не как \u-коды;
# indent=2 — файл остаётся читаемым человеком.
def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(students, file, ensure_ascii=False, indent=2)
