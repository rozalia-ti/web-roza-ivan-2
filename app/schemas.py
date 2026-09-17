# Модели Pydantic для проверки входных данных: не прошли проверку — FastAPI вернёт 422.
# здесь проверяются сами данные, а не их наличие. Например, если в POST пришёл пустой JSON {}, то FastAPI вернёт 422, потому что обязательные поля отсутствуют. Если же пришёл JSON с полями, но они не соответствуют требованиям (например, group="12345"), то тоже будет 422.
# то есть проверяется именно типизация и соответствие формату, а не наличие полей. Если поле отсутствует, то оно будет None, если оно есть, то проверяется его значение.

from datetime import date # это импортируем для работы с датами, чтобы проверять дату заселения студентов и сравнивать её с минимальной допустимой датой.

from pydantic import BaseModel, Field, field_validator # это импортируем для создания моделей данных и валидации полей. BaseModel используется для создания моделей, Field позволяет задавать ограничения на поля, а field_validator используется для создания пользовательских валидаторов для полей модели.

# Группа: одна буква и 4 цифры, например P3211
GROUP_PATTERN = r"^[A-Za-zА-Яа-я][0-9]{4}$"
# ИСУ ID: 6 цифр, третья от 1 до 5
ISU_ID_PATTERN = r"^[0-9][0-9][1-5][0-9]{3}$"
MIN_CHECK_IN_DATE = date(2020, 1, 1)


# Дата заселения: не ранее 2020-01-01. Общая для двух моделей ниже.
def validate_check_in_date(value):
    if value is not None and value < MIN_CHECK_IN_DATE:
        # ошибка монтируется в ответе FastAPI, если пользователь прислал дату заселения раньше 2020-01-01. FastAPI автоматически обрабатывает исключения и возвращает их в виде JSON с соответствующим статусом ошибки.
        raise ValueError("Срок заселения должен быть не ранее 2020-01-01")

    return value


# Модель для POST: поля без default обязательны.
class StudentCreate(BaseModel):
    fullName: str = Field(min_length=2)
    group: str = Field(pattern=GROUP_PATTERN)
    isuId: str = Field(pattern=ISU_ID_PATTERN)
    dormNumber: int = Field(ge=1)  # ge=1: больше или равно 1 ge означает "greater than or equal to" (больше или равно), то есть значение поля dormNumber должно быть больше или равно 1. Это ограничение гарантирует, что номер общежития не может быть отрицательным или нулевым.
    room: int = Field(ge=1)
    checkInDate: date
    isForeigner: bool = False
    notes: str | None = None  # необязательное поле

    # То же, что декоратор @field_validator, но в функциональном стиле —
    # чтобы переиспользовать одну функцию в двух классах.
    check_in_date_validator = field_validator("checkInDate")(validate_check_in_date)


# Модель для PATCH: все поля опциональны — не пришло поле, значит не обновляется.
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
