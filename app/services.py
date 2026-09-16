# Бизнес-логика приложения: фильтрация, проверка уникальности ИСУ ID, CRUD.
# Этот слой не знает про HTTP-маршруты — он получает данные, применяет правила
# и возвращает результат. Ошибки правил (дубликат ИСУ ID) — это HTTPException 409.

from fastapi import HTTPException

from .schemas import StudentCreate, StudentUpdate
from .storage import load_students, save_students


# Возвращает студентов, отфильтрованных по переданным свойствам.
# Сравнение по вхождению (includes), а не на точное равенство:
# str(value) in str(поле), поэтому "P32" найдёт группы P3211 и P3212,
# а "8" — общежития 8 и 18. Пустые фильтры (None) пропускаются.
# isForeigner — булево значение, для него сравнение точное.
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


# Ищет студента по идентификатору.
# Возвращает словарь студента или None, если такого id нет.
def get_student_by_id(student_id):
    for student in load_students():
        if student["id"] == student_id:
            return student

    return None


# Создаёт студента: проверяет уникальность ИСУ ID (при дубликате — 409),
# назначает id и сохраняет в файл.
# model_dump(mode="json") превращает модель в словарь, пригодный для JSON
# (например, дата становится строкой "2024-09-01").
# default=0 в max — если студентов ещё нет, максимум считается от нуля,
# и первый студент получит id = 1.
def create_student(student: StudentCreate):
    students = load_students()

    if any(item["isuId"] == student.isuId for item in students):
        raise HTTPException(status_code=409, detail="Студент с таким ИСУ ID уже существует")

    new_student = student.model_dump(mode="json")
    new_student["id"] = max((item["id"] for item in students), default=0) + 1

    students.append(new_student)
    save_students(students)

    return new_student


# Частично обновляет студента по id, возвращает обновлённого или None (не найден).
# exclude_unset=True берёт из модели только поля, реально пришедшие в запросе:
# не упомянутые в PATCH поля не перезаписываются (иначе все стали бы None).
# При смене isuId проверяем, что новый ID не занят другим студентом (409).
def update_student(student_id, student: StudentUpdate):
    students = load_students()

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


# Удаляет студента по id.
# Возвращает True, если студент был и удалён, и False, если такого id нет.
def delete_student(student_id):
    students = load_students()
    remaining = [student for student in students if student["id"] != student_id]

    if len(remaining) == len(students):
        return False

    save_students(remaining)

    return True
