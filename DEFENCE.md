# Защита лабораторной работы №2 — Backend (REST API)

Фронтенд (лаба №1) уже защищён, здесь — только серверная часть: REST API на **FastAPI**
для управления студентами общежития. Клиентский интерфейс переделан в stateless:
вся бизнес-логика (валидация, хранение, id) переехала на сервер.

---

## 1. Архитектура: разделение по слоям

Требование задания: маршруты, бизнес-логика и работа с данными — в отдельных файлах.

```
app/
├── __init__.py  — пустой маркер: превращает папку в пакет Python
├── main.py      — точка входа: сборка приложения, обработчики ошибок, статика
├── routes.py    — маршруты (слой маршрутизации)
├── services.py  — бизнес-логика
├── storage.py   — работа с данными (JSON-файл)
└── schemas.py   — модели Pydantic (валидация входных данных)
```

Поток запроса всегда один:

```
запрос → routes.py → services.py → storage.py → data.json
ответ  ← routes.py ← services.py (dict) ← FastAPI сериализует в JSON
```

Каждый слой знает только про соседний: `routes` не лезет в файл, `storage` не знает
про HTTP. `__init__.py` нужен, чтобы работали импорты `from .routes import router`
и запуск `uvicorn app.main:app`.

Запуск:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --port 8000
```

---

## 2. Модель студента и серверная валидация (`schemas.py`)

Модель та же, что в лабе №1, но проверка теперь на сервере. Используются
**Pydantic-модели** — FastAPI автоматически десериализует JSON-тело запроса
в модель и валидирует его до запуска обработчика.

```python
class StudentCreate(BaseModel):
    fullName: str = Field(min_length=2)
    group: str = Field(pattern=GROUP_PATTERN)      # ^[A-Za-zА-Яа-я][0-9]{4}$
    isuId: str = Field(pattern=ISU_ID_PATTERN)     # ^[0-9][0-9][1-5][0-9]{3}$
    dormNumber: int = Field(ge=1)
    room: int = Field(ge=1)
    checkInDate: date
    isForeigner: bool = False
    notes: str | None = None
```

Ключевые моменты:

- **Аннотации типов**: `str`, `int`, `date`, `bool`, `str | None` (union-тип, PEP 604).
  Pydantic по ним проверяет данные: `"8"` вместо числа или `"abc"` вместо даты → 422.
- **`Field(...)`** задаёт ограничения: `min_length=2` (ФИО), `pattern=` (регулярки для
  группы и ИСУ ID), `ge=1` (greater or equal — номера общежития и комнаты).
- **Две модели**: `StudentCreate` — для POST, поля без `default` обязательны;
  `StudentUpdate` — для PATCH, все поля опциональны (`str | None = None`):
  не пришло поле → равно `None` → не обновляется.
- **Проверка даты** — через `field_validator`, она нужна обеим моделям, поэтому
  вынесена в общую функцию:

```python
def validate_check_in_date(value):
    if value is not None and value < MIN_CHECK_IN_DATE:
        raise ValueError("Срок заселения должен быть не ранее 2020-01-01")
    return value

# в классе — прикрепление к полю (то же, что декоратор @field_validator):
check_in_date_validator = field_validator("checkInDate")(validate_check_in_date)
```

Почему Pydantic, а не dataclass: dataclass только хранит данные, pydantic ещё и
**валидирует** их при создании и умеет сериализовать обратно в JSON (`model_dump`).

---

## 3. Маршруты (`routes.py`)

Все эндпоинты из задания, с префиксом `/api/requests`:

| Метод   | Путь                  | Что делает                          | Код успеха |
|---------|-----------------------|-------------------------------------|-----------|
| GET     | `/api/requests`       | список + фильтрация через query     | 200       |
| GET     | `/api/requests/:id`   | один студент                        | 200       |
| POST    | `/api/requests`       | создать                             | 201       |
| PATCH   | `/api/requests/:id`   | частичное обновление                | 200       |
| DELETE  | `/api/requests/:id`   | удалить                             | 204       |
| QUERY   | `/api/requests/:id`   | запрос студента (из задания)        | 200       |

Обработчики — обычные функции с декораторами:

```python
@router.get("/{student_id}")
def get_student(student_id: int):
    student = services.get_student_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student
```

- **Path-параметр**: `{student_id}` из URL становится аргументом `student_id: int`.
  Нечисловой id (`/api/requests/abc`) FastAPI сам отклоняет с 422.
- **Query-параметры** — аргументы функции списка, все опциональные:

```python
@router.get("")
def list_students(
    fullName: str | None = None,
    group: str | None = None,
    dormitory: int | None = None,   # имя из задания, внутри = поле dormNumber
    ...
):
    return services.get_students(filters)
```

  Запрос `GET /api/requests?group=P32&dormitory=8` → в `filters` попадают
  `{"group": "P32", "dormNumber": 8}`, остальные — `None`.
- **QUERY** — метод из задания; у FastAPI нет готового декоратора, поэтому
  `@router.api_route("/{student_id}", methods=["QUERY"])`. Работает как GET.
- **Декораторы** здесь — ключевой механизм FastAPI: `@router.get(...)` регистрирует
  функцию как обработчик метода+пути, `@app.exception_handler(...)` — как обработчик
  исключений. Декоратор — функция, принимающая функцию и возвращающая обёртку.

---

## 4. Бизнес-логика (`services.py`)

**Фильтрация по вхождению (includes)**, а не по точному совпадению:

```python
if isinstance(value, bool):
    students = [student for student in students if student.get(key) == value]
else:
    students = [student for student in students if str(value) in str(student.get(key))]
```

`"P32"` найдёт группы P3211 и P3212, `"8"` — общежития 8 и 18. Булево `isForeigner`
сравнивается точно. Здесь же — списковые включения и генераторные выражения
(`any(... for ... in ...)`, `max(... for ... in ...)`).

**Уникальность ИСУ ID** (обязательное требование) — при создании и при смене в PATCH:

```python
if any(item["isuId"] == student.isuId for item in students):
    raise HTTPException(status_code=409, detail="Студент с таким ИСУ ID уже существует")
```

**Создание**: id назначает сервер — максимальный существующий + 1:

```python
new_student = student.model_dump(mode="json")
new_student["id"] = max((item["id"] for item in students), default=0) + 1
```

`model_dump(mode="json")` превращает модель в словарь, пригодный для JSON
(например, `date` → строка `"2024-09-01"`). `default=0` — если список пуст,
первый студент получит id = 1.

**PATCH — частичное обновление**:

```python
current.update(student.model_dump(mode="json", exclude_unset=True))
```

`exclude_unset=True` берёт из модели только поля, реально пришедшие в запросе.
Без него все необязательные поля стали бы `None` и затёрли бы данные студента.

---

## 5. Хранение и stateless (`storage.py`)

Данные — в JSON-файле `data.json` (второй разрешённый вариант задания — память):

```python
def load_students():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(students, file, ensure_ascii=False, indent=2)
```

**Stateless**: сервер не хранит ничего между запросами — ни сессий, ни состояния
в памяти. Каждый запрос обрабатывается независимо: прочитал `data.json` → изменил →
записал. Всё состояние приложения — в файле. Поэтому сервер можно перезапустить
или запустить несколько копий — данные не потеряются.

---

## 6. Единый формат ошибок (`main.py`)

Все ошибки — в одном виде `{"error": "текст"}`. За это отвечают три обработчика:

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    ...  # тексты ошибок склеиваются через "; "
    return JSONResponse(status_code=422, content={"error": "; ".join(messages)})

@app.exception_handler(Exception)
async def internal_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Внутренняя ошибка сервера"})
```

Используемые коды (тема «HTTP-методы и коды состояния»):

| Код | Когда |
|-----|-------|
| 200 | успешный GET / PATCH / QUERY |
| 201 | POST — студент создан |
| 204 | DELETE — удалён (ответ без тела) |
| 400 | тело запроса — битый JSON (плохой синтаксис) |
| 404 | студент по id не найден |
| 409 | конфликт: ИСУ ID уже занят |
| 422 | данные не прошли валидацию (pydantic) |
| 500 | непредвиденная ошибка сервера |

Разница 400 vs 422: 400 — запрос вообще не разобрать (сломанный JSON),
422 — запрос понятен, но данные неверны (группа не подходит под шаблон).
В обработчике валидации это определяется по типу ошибки `json_*`.

Обработчики — `async`: FastAPI построен на asyncio (ASGI), обработчики ошибок
асинхронные, а наша бизнес-логика синхронная — FastAPI выполняет её в пуле потоков,
блокировок event loop нет.

Раздача фронтенда — тоже в `main.py`:

```python
app.mount("/", StaticFiles(directory=... / "static", html=True), name="static")
```

`GET /` отдаёт `static/index.html` (html=True — index для корня). API не перекрывается:
маршруты `/api/...` зарегистрированы раньше монтирования и проверяются первыми.

---

## 7. Как Python общается с JavaScript

Напрямую — никак. Единственная точка контакта — HTTP с JSON:

- JS (`fetch`) отправляет запрос: фильтры — в query-параметрах, данные — в теле
  `JSON.stringify(student)`, id — в path (`/api/requests/5`);
- FastAPI десериализует JSON в Pydantic-модель (валидация) → `dict` в ответе
  сериализуется обратно в JSON;
- JS делает `response.json()` и рисует таблицу; ошибки читает из `data.error`.

---

## 8. Быстрые ответы на вопросы защиты

1. **Python в серверной веб-разработке** — язык со богатой стандартной библиотекой
   (json, http, datetime), огромной экосистемой; у нас: чтение/запись JSON, pathlib.
2. **Фреймворки** — FastAPI (наш выбор: асинхронный, pydantic-валидация из коробки,
   автодокументация), Flask — синхронный и минималистичный, DRF — тяжёлый, для
   больших проектов поверх Django.
3. **Типизация** — аннотации `str`, `int`, `date`, `str | None` во всех сигнатурах
   (`routes.py`, `schemas.py`); FastAPI по ним парсит и проверяет данные.
4. **Модели данных** — Pydantic `BaseModel` (валидация + сериализация), а не dataclass
   (только хранение) и не словарь (нет проверки).
5. **Исключения** — `HTTPException` (404/409) бросается в логике, ловится глобальным
   обработчиком; `ValueError` в валидаторе pydantic превращает в 422; `Exception` — 500.
6. **Декораторы** — `@router.get(...)`, `@router.post(...)` регистрируют обработчики,
   `@app.exception_handler(...)` — обработчики ошибок.
7. **Контекст запроса** — каждый запрос получает свой `Request`, данные не «протекают»
   между запросами, общее только `data.json`.
8. **Синхронный/асинхронный код** — обработчики ошибок `async def`, логика синхронная;
   uvicorn — ASGI-сервер на asyncio.
9. **Итераторы, генераторы** — генераторные выражения в `services.py`:
   `any(... for ...)`, `max(... for ...)`; списковые включения для фильтрации.
10. **Модули, пакеты** — пакет `app/` (`__init__.py`), слои в отдельных модулях,
    импорты `from .routes import router`.
11. **REST** — ресурсы (студенты) с URL `/api/requests`, методы как глаголы,
    JSON-представление, stateless.
12. **HTTP-методы и коды** — таблица в разделе 6.
13. **Маршрутизация** — path-параметры `{student_id}`, query-параметры `?group=P32`.
14. **JSON** — `json.load`/`json.dump` (storage), `JSON.stringify`/`response.json()` (JS),
    `model_dump(mode="json")` (pydantic).
15. **Серверная валидация** — pydantic-модели + `field_validator`, ошибки 422 в едином
    формате.
16. **Stateless** — раздел 5.
17. **Хранение и фильтрация** — JSON-файл, фильтрация по вхождению в `services.py`.
18. **CRUD и идентификация** — Create/Read/Update/Delete = POST/GET/PATCH/DELETE,
    у каждого студента числовой `id` (сервер) и уникальный `isuId` (проверка на 409).
