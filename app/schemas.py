# Модели данных (Pydantic) для проверки входных данных.
# Pydantic сам проверяет типы и ограничения полей: если данные в JSON не проходят
# проверку, FastAPI отклоняет запрос с кодом 422, не запуская обработчик.

from datetime import date

from pydantic import BaseModel, Field, field_validator

# Шаблон группы: одна буква (латиница или кириллица) и 4 цифры, например P3211
GROUP_PATTERN = r"^[A-Za-zА-Яа-я][0-9]{4}$"
# Шаблон ИСУ ID: 6 цифр, третья цифра от 1 до 5
ISU_ID_PATTERN = r"^[0-9][0-9][1-5][0-9]{3}$"
# Минимально допустимая дата заселения
MIN_CHECK_IN_DATE = date(2020, 1, 1)


# Проверка срока заселения: не ранее 2020-01-01.
# Вынесена в отдельную функцию, потому что нужна обеим моделям ниже.
# Если поле не передано (value is None) — проверять нечего, пропускаем.
def validate_check_in_date(value):
    if value is not None and value < MIN_CHECK_IN_DATE:
        raise ValueError("Срок заселения должен быть не ранее 2020-01-01")

    return value


# Модель для POST /api/requests — создание студента.
# Поля без значения по умолчанию обязательны: если их нет в теле запроса, будет 422.
class StudentCreate(BaseModel):
    fullName: str = Field(min_length=2)  # ФИО: не короче 2 символов
    group: str = Field(pattern=GROUP_PATTERN)  # группа должна подходить под шаблон
    isuId: str = Field(pattern=ISU_ID_PATTERN)  # ИСУ ID должен подходить под шаблон
    dormNumber: int = Field(ge=1)  # ge=1: значение должно быть больше или равно 1
    room: int = Field(ge=1)
    checkInDate: date  # Pydantic сам разбирает строку "2024-09-01" в дату
    isForeigner: bool = False  # если поле не пришло — будет False
    notes: str | None = None  # необязательное поле: нет в JSON — будет None

    # Прикрепляем проверку даты к полю checkInDate.
    # Это то же самое, что декоратор @field_validator("checkInDate"),
    # только записанное в функциональном стиле — чтобы переиспользовать
    # одну функцию в двух классах без дублирования кода.
    check_in_date_validator = field_validator("checkInDate")(validate_check_in_date)


# Модель для PATCH /api/requests/:id — частичное обновление.
# Все поля опциональны (тип | None и default=None): если поле не пришло в запросе,
# оно равно None и не обновляется. Ограничения (pattern, ge, min_length)
# проверяются только для тех полей, которые реально передали.
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
