# Backend каталога товаров

Python 3.13, FastAPI, PostgreSQL, sync SQLAlchemy 2.x, Pydantic v2,
psycopg 3, PyJWT и bcrypt через pwdlib. Посетители читают каталог без
авторизации; администратор создаёт, изменяет и удаляет товары с Bearer JWT.

## Установка

Из корня проекта:

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell: `.venv\Scripts\Activate.ps1`.
В этом проекте уже есть окружение `app/venv`; вместо создания нового можно
выполнить `source app/venv/bin/activate` и установить те же зависимости.
Файл `app/requirements.txt` оставлен как ссылка на основной `requirements.txt`.

## Настройка `.env`

При новой установке:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Вставьте сгенерированное значение в `JWT_SECRET_KEY` и задайте пароль администратора.
Пример настроек для локальной разработки:

```dotenv
DATABASE_URL=postgresql+psycopg://shop_user:shop_password@localhost:5432/shop_db
JWT_SECRET_KEY=replace_with_a_random_secret_at_least_32_bytes
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
FRONTEND_URL=http://localhost:5173
```

Существующий `app/.env` тоже поддерживается и уже дополнен недостающими
настройками и случайным JWT-секретом. Не нужно копировать `.env.example` поверх
него. Порядок приоритета: переменные процесса, `backend/.env`, `backend/app/.env`.
Пути к `.env` определяются относительно файлов приложения, а не текущей папки.
`JWT_SECRET_KEY` должен содержать минимум 32 байта. Пароль bcrypt ограничен
72 байтами UTF-8; пароль не обрезается. Пароли и JWT-секреты не находятся в коде.

## PostgreSQL

Создать локальный сервер PostgreSQL 16:

```bash
docker run -d \
  --name shop-postgres \
  -e POSTGRES_DB=shop_db \
  -e POSTGRES_USER=shop_user \
  -e POSTGRES_PASSWORD=shop_password \
  -p 5432:5432 \
  -v shop-postgres-data:/var/lib/postgresql/data \
  postgres:16
```

Если контейнер уже создан, достаточно `docker start shop-postgres`.
Проверка готовности:

```bash
docker exec shop-postgres pg_isready -U shop_user -d shop_db
```

Значение `DATABASE_URL` для этого примера:
`postgresql+psycopg://shop_user:shop_password@localhost:5432/shop_db`.
Если пароль содержит специальные символы URL, их нужно percent-encode.

## Запуск

Из `backend/`, в активированном окружении:

```bash
uvicorn app.main:app --reload
```

Swagger: <http://127.0.0.1:8000/docs>.
Проверка: <http://127.0.0.1:8000/> возвращает `{"status":"ok"}`.

При старте lifespan импортирует модели, вызывает
`Base.metadata.create_all(bind=engine)` и создаёт администратора из `.env`,
если его username отсутствует. Пароль в БД хранится только как bcrypt-хеш.
Повторный запуск не меняет пароль или активность существующего администратора;
изменение `ADMIN_PASSWORD` в `.env` не сбрасывает его пароль.
`create_all()` создаёт отсутствующие таблицы, но не изменяет существующие столбцы.

## Авторизация

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

Ответ:

```json
{"access_token":"<JWT>","token_type":"bearer"}
```

Замените пароль в запросе, если настроили другой `ADMIN_PASSWORD`.
Неверные данные и неактивный администратор возвращают одинаковый ответ
`401 {"detail":"Invalid credentials"}`.
JWT содержит `sub` (ID администратора), `username` и `exp`, срок по умолчанию — 1440 минут.

В Swagger выполните login, скопируйте `access_token`, нажмите **Authorize**
и вставьте только токен, без префикса `Bearer`. Swagger добавит префикс сам.
При запросе вручную заголовок выглядит так:

```http
Authorization: Bearer <JWT>
```

Отсутствующий, некорректный или просроченный токен, удалённый или неактивный
администратор возвращают `401` с `WWW-Authenticate: Bearer`.

## API

| Метод | URL | Доступ | Результат |
| --- | --- | --- | --- |
| GET | `/` | Публичный | Статус приложения |
| POST | `/api/auth/login` | Публичный | JWT по JSON username/password |
| GET | `/api/products?skip=0&limit=50` | Публичный | Массив товаров |
| GET | `/api/products/{product_id}` | Публичный | Один товар |
| POST | `/api/admin/products` | Bearer JWT | Новый товар, статус 201 |
| PATCH | `/api/admin/products/{product_id}` | Bearer JWT | Частичное обновление |
| DELETE | `/api/admin/products/{product_id}` | Bearer JWT | `{"message":"Product deleted"}` |

`skip >= 0`, `limit` от 1 до 100 (по умолчанию 50), сортировка по ID.
Несуществующий товар: `404 {"detail":"Product not found"}`.
Ошибки валидации: `422`.

### Создание товара

```bash
curl -X POST http://127.0.0.1:8000/api/admin/products \
  -H 'Authorization: Bearer <JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Laptop","description":"Good laptop","price":1000,"image_url":"https://example.com/image.jpg"}'
```

`title` обязателен, пробелы по краям удаляются, пустая строка запрещена,
максимум 255 символов. `price` обязателен, неотрицателен, хранится как
`Numeric(12, 2)` и принимает максимум 10 цифр до и 2 после точки.
Ответ содержит цену строкой с двумя знаками, например `"1000.00"`,
чтобы избежать потери точности при обработке денег в JavaScript.
`description` и `image_url` необязательны; `image_url` до 1000 символов.
Даты `created_at` и `updated_at` создаются автоматически в БД.

### Обновление и удаление

```bash
curl -X PATCH http://127.0.0.1:8000/api/admin/products/1 \
  -H 'Authorization: Bearer <JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"price":"950.00","description":null}'

curl -X DELETE http://127.0.0.1:8000/api/admin/products/1 \
  -H 'Authorization: Bearer <JWT>'
```

Пропущенные поля не меняются. `null` очищает `description` или `image_url`;
`title` и `price` не могут быть `null`. Пустой PATCH возвращает текущий товар.
`updated_at` обновляется SQLAlchemy при фактическом изменении товара через API.
CORS разрешает origin из `FRONTEND_URL`, включая заголовок Authorization.

## Проверка

```bash
python -m pip install -r requirements-dev.txt
ruff check app tests
ruff format --check app tests
```

Интеграционные тесты работают с настоящим PostgreSQL. Задайте
`TEST_DATABASE_URL` (с драйвером `postgresql+psycopg`); пользователь БД должен
иметь право создавать схемы. Подойдёт локальная БД из Docker-примера:

```bash
TEST_DATABASE_URL='postgresql+psycopg://shop_user:shop_password@localhost:5432/shop_db' \
  python -m pytest -q
```

Тесты создают отдельную случайную схему `catalog_test_<uuid>` и удаляют её
после выполнения. Таблицы каталога в основной схеме не изменяются.
Без `TEST_DATABASE_URL` интеграционные тесты пропускаются.
Проверяются создание таблиц и администратора, bcrypt, login/JWT,
публичное чтение и пагинация, полный CRUD, валидация, CORS и Swagger BearerAuth,
а также отсутствующие, поддельные и просроченные токены и отключённые администраторы.

## Структура

```text
backend/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── tests/
│   ├── conftest.py
│   └── test_api.py
└── app/
    ├── .env                 # существующая локальная конфигурация
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── main.py
    ├── requirements.txt     # совместимость с прежним расположением
    ├── core/
    │   ├── __init__.py
    │   ├── dependencies.py
    │   └── security.py
    ├── models/
    │   ├── __init__.py
    │   ├── admin.py
    │   └── product.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── auth.py
    │   └── product.py
    ├── routers/
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── auth.py
    │   └── products.py
    └── services/
        ├── __init__.py
        ├── auth.py
        └── products.py
```

Новые пакеты заменяют пустые заготовки `app/models.py`, `app/schemas.py`
и `app/auth.py`. Frontend не менялся, Alembic не используется.
