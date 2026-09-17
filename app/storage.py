# Слой данных: чтение и запись студентов в JSON-файл.

import json
from pathlib import Path

# data.json в папке проекта (на два уровня выше этого файла)
# Вот этот путь нам пригодится для хранения и загрузки данных студентов. Мы используем Path из pathlib для удобной работы с файловой системой, чтобы указать путь к файлу data.json, который находится на два уровня выше текущего файла storage.py.
DATA_FILE = Path(__file__).resolve().parent.parent / "data.json"


# Загружает всех студентов из файла, возвращает список словарей. Если файла нет — пустой список.
def load_students():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# Сохраняет список в файл целиком. ensure_ascii=False — русский текст как есть.
def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        # записываем то, что получили из функции в файл, используя json.dump. ensure_ascii=False позволяет сохранять русский текст в читаемом виде, а indent=2 делает JSON более читаемым с отступами.
        json.dump(students, file, ensure_ascii=False, indent=2)
