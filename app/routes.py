# Маршруты REST API (слой маршрутизации).
# Каждый обработчик достаёт данные из запроса, передаёт их в бизнес-логику
# (services) и формирует HTTP-ответ. Самой логики здесь почти нет.

from fastapi import APIRouter, HTTPException

from . import services
from .schemas import StudentCreate, StudentUpdate

# Все маршруты ниже начинаются с префикса /api/requests
router = APIRouter(prefix="/api/requests")


# GET /api/requests — список студентов.
# Параметры берутся из query-строки: /api/requests?group=P32&dormitory=8
# dormitory — имя параметра из задания, внутри оно соответствует полю dormNumber.
# Не переданные параметры равны None и не участвуют в фильтрации.
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


# GET /api/requests/:id — один студент по идентификатору.
# student_id объявлен как int: нечисловой id (например /api/requests/abc)
# FastAPI сам отклонит с 422. Если студент не найден — 404.
@router.get("/{student_id}")
def get_student(student_id: int):
    student = services.get_student_by_id(student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return student


# POST /api/requests — создать студента.
# Тело запроса проверяется моделью StudentCreate (невалидное — 422),
# при успехе возвращается созданный студент с кодом 201.
@router.post("", status_code=201)
def create_student(student: StudentCreate):
    return services.create_student(student)


# PATCH /api/requests/:id — частичное обновление:
# в теле достаточно передать только изменяемые поля.
@router.patch("/{student_id}")
def update_student(student_id: int, student: StudentUpdate):
    updated = services.update_student(student_id, student)

    if updated is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return updated


# DELETE /api/requests/:id — удалить студента.
# При успехе ответ пустой (тела у 204 быть не должно).
@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int):
    if not services.delete_student(student_id):
        raise HTTPException(status_code=404, detail="Студент не найден")


# QUERY /api/requests/:id — метод QUERY из задания.
# api_route нужен потому, что у FastAPI нет готового декоратора @router.query.
# Работает как GET: возвращает студента по id или 404.
@router.api_route("/{student_id}", methods=["QUERY"])
def query_student(student_id: int):
    student = services.get_student_by_id(student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return student
