from fastapi import HTTPException

from .schemas import StudentCreate, StudentUpdate
from .storage import load_students, save_students


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


def get_student_by_id(student_id):
    for student in load_students():
        if student["id"] == student_id:
            return student

    return None


def create_student(student: StudentCreate):
    students = load_students()

    if any(item["isuId"] == student.isuId for item in students):
        raise HTTPException(status_code=409, detail="Студент с таким ИСУ ID уже существует")

    new_student = student.model_dump(mode="json")
    new_student["id"] = max((item["id"] for item in students), default=0) + 1

    students.append(new_student)
    save_students(students)

    return new_student


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


def delete_student(student_id):
    students = load_students()
    remaining = [student for student in students if student["id"] != student_id]

    if len(remaining) == len(students):
        return False

    save_students(remaining)

    return True
