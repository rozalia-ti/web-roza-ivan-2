# Бизнес-логика: фильтрация, уникальность ИСУ ID, CRUD.
# Цепочка запроса: routes.py → services.py → storage.py. Stateless: всё состояние в data.json.

from fastapi import HTTPException

from .schemas import StudentCreate, StudentUpdate # импортируем схемы для создания и обновления студентов. Схемы нам нужны для того, чтобы проверять входные данные на соответствие требованиям (например, типы данных, обязательные поля и т.д.) перед тем, как мы будем их использовать в нашей бизнес-логике.
from .storage import load_students, save_students


# Список с фильтрами. Сравнение по вхождению (includes): "P32" найдёт P3211 и P3212.
# isForeigner — булево, сравнивается точно. Пустые фильтры (None) пропускаются.
# эта функция используется в routes.py для обработки GET-запроса на /api/requests с фильтрами в query-параметрах.
# query-параметры становятся ее аргументами, которые она передает в filters словарь, затем фильтрует студентов по этим параметрам и возвращает список студентов, соответствующих фильтрам.
def get_students(filters):
    students = load_students()

    for key, value in filters.items():
        if value is None:
            continue

        if isinstance(value, bool):
            students = [student for student in students if student.get(key) == value]
        else:
            students = [student for student in students if str(value) in str(student.get(key))]

    return students


# Студент по id или None, если не найден.
def get_student_by_id(student_id):
    for student in load_students():
        if student["id"] == student_id:
            return student

    return None


# Создание: дубликат ИСУ ID → 409; id = максимальный существующий + 1 (default=0 — для пустого списка).
# model_dump(mode="json") — модель в словарь, пригодный для JSON (дата → строка).
def create_student(student: StudentCreate):
    students = load_students()

    if any(item["isuId"] == student.isuId for item in students):
        raise HTTPException(status_code=409, detail="Студент с таким ИСУ ID уже существует")

    new_student = student.model_dump(mode="json")
    new_student["id"] = max((item["id"] for item in students), default=0) + 1

    students.append(new_student)
    save_students(students)

    return new_student


# Частичное обновление: exclude_unset=True берёт только пришедшие в запросе поля —
# не упомянутое в PATCH поле не перезаписывается. Нет студента → None.
def update_student(student_id, student: StudentUpdate):
    students = load_students()
# этот цикл ищет студента по id, если находит, проверяет уникальность isuId и обновляет поля, затем сохраняет в файл. Если не находит, возвращает None.
    for current in students:
        if current["id"] != student_id:
            continue

        if student.isuId is not None and any(
            item["isuId"] == student.isuId and item["id"] != student_id for item in students
        ):
            raise HTTPException(status_code=409, detail="Студент с таким ИСУ ID уже существует")

        current.update(student.model_dump(mode="json", exclude_unset=True))
        save_students(students)

        return current

    return None


# Удаление: True если студент был, False если id нет.
def delete_student(student_id):
    students = load_students()
    # оставить только тех, кто не равен удаляемому. 
    remaining = [student for student in students if student["id"] != student_id]
    # если мы никого не удалили то такого студента и не было , возвращаем False     
    if len(remaining) == len(students):
        return False
    # сохраняем оставшихся студентов в файл
    save_students(remaining)

    return True
