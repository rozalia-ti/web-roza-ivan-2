from fastapi import APIRouter, HTTPException

from . import services
from .schemas import StudentCreate, StudentUpdate

router = APIRouter(prefix="/api/requests")


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


@router.get("/{student_id}")
def get_student(student_id: int):
    student = services.get_student_by_id(student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return student


@router.post("", status_code=201)
def create_student(student: StudentCreate):
    return services.create_student(student)


@router.patch("/{student_id}")
def update_student(student_id: int, student: StudentUpdate):
    updated = services.update_student(student_id, student)

    if updated is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return updated


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int):
    if not services.delete_student(student_id):
        raise HTTPException(status_code=404, detail="Студент не найден")


@router.api_route("/{student_id}", methods=["QUERY"])
def query_student(student_id: int):
    student = services.get_student_by_id(student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return student
