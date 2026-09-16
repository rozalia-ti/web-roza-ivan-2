from datetime import date

from pydantic import BaseModel, Field, field_validator

GROUP_PATTERN = r"^[A-Za-zА-Яа-я][0-9]{4}$"
ISU_ID_PATTERN = r"^[0-9][0-9][1-5][0-9]{3}$"
MIN_CHECK_IN_DATE = date(2020, 1, 1)


def validate_check_in_date(value):
    if value is not None and value < MIN_CHECK_IN_DATE:
        raise ValueError("Срок заселения должен быть не ранее 2020-01-01")

    return value


class StudentCreate(BaseModel):
    fullName: str = Field(min_length=2)
    group: str = Field(pattern=GROUP_PATTERN)
    isuId: str = Field(pattern=ISU_ID_PATTERN)
    dormNumber: int = Field(ge=1)
    room: int = Field(ge=1)
    checkInDate: date
    isForeigner: bool = False
    notes: str | None = None

    check_in_date_validator = field_validator("checkInDate")(validate_check_in_date)


class StudentUpdate(BaseModel):
    fullName: str | None = Field(default=None, min_length=2)
    group: str | None = Field(default=None, pattern=GROUP_PATTERN)
    isuId: str | None = Field(default=None, pattern=ISU_ID_PATTERN)
    dormNumber: int | None = Field(default=None, ge=1)
    room: int | None = Field(default=None, ge=1)
    checkInDate: date | None = None
    isForeigner: bool | None = None
    notes: str | None = None

    check_in_date_validator = field_validator("checkInDate")(validate_check_in_date)
