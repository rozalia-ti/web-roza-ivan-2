# Маршруты REST API: достают данные из запроса, зовут services, формируют ответ.
# FastAPI сам десериализует JSON-тело в Pydantic-модель, query-параметры — в аргументы,
# path-параметр {student_id} — в аргумент student_id; dict в ответе сериализуется в JSON.

from fastapi import APIRouter, HTTPException

from . import services
from .schemas import StudentCreate, StudentUpdate

# Все маршруты начинаются с /api/requests
router = APIRouter(prefix="/api/requests")


# GET — список студентов; фильтры из query: ?group=P32&dormitory=8
# (dormitory — имя из задания, соответствует полю dormNumber).
@router.get("")
def list_students(
    fullName: str | None = None,
    group: str | None = None,
    isuId: str | None = None,
    dormitory: int | None = None,
    room: int | None = None,
    checkInDate: str | None = None,
    isForeigner: bool | None = None,
):
    filters = {
        "fullName": fullName,
        "group": group,
        "isuId": isuId,
        "dormNumber": dormitory,
        "room": room,
        "checkInDate": checkInDate,
        "isForeigner": isForeigner,
    }

    return services.get_students(filters)


# GET — студент по id или 404 (нечисловой id FastAPI сам отклонит с 422).
@router.get("/{student_id}")
def get_student(student_id: int):
    student = services.get_student_by_id(student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return student


# POST — создать студента; тело проверяет StudentCreate, при успехе 201.
@router.post("", status_code=201)
def create_student(student: StudentCreate):
    return services.create_student(student)


# PATCH — частичное обновление: достаточно только изменённых полей.
@router.patch("/{student_id}")
def update_student(student_id: int, student: StudentUpdate):
    updated = services.update_student(student_id, student)

    if updated is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return updated


# DELETE — удалить студента; 204 идёт без тела.
@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int):
    if not services.delete_student(student_id):
        raise HTTPException(status_code=404, detail="Студент не найден")


# QUERY — метод из задания; api_route нужен, т.к. готового декоратора @query нет. Работает как GET.
@router.api_route("/{student_id}", methods=["QUERY"])
def query_student(student_id: int):
    student = services.get_student_by_id(student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return student
