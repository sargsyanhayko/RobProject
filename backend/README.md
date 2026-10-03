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
Для уже созданного каталога приложение дополнительно добавляет отсутствующие
столбцы `image_data BYTEA` и `image_content_type VARCHAR(100)` через
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Обновление выполняется при старте,
сохраняет товары и не требует Alembic. Пользователь БД должен владеть таблицей
`products`, чтобы добавлять столбцы.

Категории обновляются ещё одним startup helper в одной транзакции:
он добавляет `category VARCHAR(50)`, заполняет `NULL` значением `other`,
затем устанавливает `NOT NULL` и CHECK для пяти допустимых категорий.
Все товары из старой таблицы получают `other`, их поля и фотографии сохраняются.
Повторные запуски не меняют уже назначенные категории. Ручной SQL и Alembic
не нужны: достаточно перезапустить backend с обновлённым кодом.

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
| GET | `/api/products?category=animals` | Публичный | Товары выбранной категории |
| GET | `/api/products/{product_id}` | Публичный | Один товар |
| GET | `/api/products/{product_id}/image` | Публичный | Фото из PostgreSQL |
| POST | `/api/admin/products` | Bearer JWT | Новый товар, статус 201 |
| POST | `/api/admin/products/upload` | Bearer JWT | Товар с локальным фото, multipart/form-data |
| PATCH | `/api/admin/products/{product_id}` | Bearer JWT | Частичное обновление |
| PATCH | `/api/admin/products/{product_id}/upload` | Bearer JWT | Поля формы и замена фото, multipart/form-data |
| DELETE | `/api/admin/products/{product_id}` | Bearer JWT | `{"message":"Product deleted"}` |

`skip >= 0`, `limit` от 1 до 100 (по умолчанию 50), сортировка по ID.
Несуществующий товар: `404 {"detail":"Product not found"}`.
Ошибки валидации: `422`.

Допустимые `category`: `animals`, `wall`, `3d_wall`, `home`, `other`.
Без query-параметра `category` возвращаются все категории; значение `all`
передавать в API не нужно. Фильтрация выполняется в БД до пагинации.
Неизвестное значение, включая пустую строку, возвращает `422`.
Категория присутствует в каждом ответе со списком или отдельным товаром.

### Создание товара

```bash
curl -X POST http://127.0.0.1:8000/api/admin/products \
  -H 'Authorization: Bearer <JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Laptop","description":"Good laptop","price":1000,"image_url":"https://example.com/image.jpg","category":"home"}'
```

`title` обязателен, пробелы по краям удаляются, пустая строка запрещена,
максимум 255 символов. `price` обязателен, неотрицателен, хранится как
`Numeric(12, 2)` и принимает максимум 10 цифр до и 2 после точки.
Ответ содержит цену строкой с двумя знаками, например `"1000.00"`,
чтобы избежать потери точности при обработке денег в JavaScript.
`description` и `image_url` необязательны; `image_url` до 1000 символов.
`category` обязательна и принимает только одно из пяти допустимых значений.
Даты `created_at` и `updated_at` создаются автоматически в БД.

### Обновление и удаление

```bash
curl -X PATCH http://127.0.0.1:8000/api/admin/products/1 \
  -H 'Authorization: Bearer <JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"price":"950.00","description":null,"category":"other"}'

curl -X DELETE http://127.0.0.1:8000/api/admin/products/1 \
  -H 'Authorization: Bearer <JWT>'
```

Пропущенные поля не меняются. `null` очищает `description` или `image_url`;
`title`, `price` и `category` не могут быть `null`.
Категория в PATCH необязательна: пропущенное поле сохраняет текущую категорию.
Пустой PATCH возвращает текущий товар.
`updated_at` обновляется SQLAlchemy при фактическом изменении товара через API.
CORS разрешает origin из `FRONTEND_URL`, включая заголовок Authorization.

### Загрузка фото с компьютера

Загруженное фото хранится непосредственно в PostgreSQL, в `products.image_data`
типа `BYTEA`. Тип содержимого хранится в `image_content_type`. `image_url`
в ответе содержит путь API, например `/api/products/1/image`; это адрес получения
сохранённого фото. Сам файл не передаётся внутри JSON со списком товаров.
При удалении товара его фото удаляется вместе с записью.

Создание товара с локальным файлом:

```bash
curl -X POST http://127.0.0.1:8000/api/admin/products/upload \
  -H 'Authorization: Bearer <JWT>' \
  -F 'title=Laptop' \
  -F 'price=1000.00' \
  -F 'category=home' \
  -F 'description=Good laptop' \
  -F 'file=@/absolute/path/to/photo.jpg'
```

Замена фотографии и сохранение полей формы:

```bash
curl -X PATCH http://127.0.0.1:8000/api/admin/products/1/upload \
  -H 'Authorization: Bearer <JWT>' \
  -F 'title=Laptop' \
  -F 'price=950.00' \
  -F 'category=other' \
  -F 'description=Updated description' \
  -F 'file=@/absolute/path/to/new-photo.png'
```

В этих multipart-endpoints обязательны `title`, `price` и `file`.
При создании также обязательна `category`; при обновлении её можно пропустить,
чтобы сохранить текущую категорию, или передать новое допустимое значение.
`description` необязателен; пустое или пропущенное значение очищает описание.
Поля и фото сохраняются в одной транзакции. Если файл или данные невалидны,
товар не создаётся, а при обновлении сохраняются предыдущие поля и фото.
Для изменения текста без замены фото используйте обычный JSON PATCH.
Для удаления только фотографии отправьте JSON PATCH `{"image_url":null}`.

Поддерживаются JPEG, PNG, WebP и GIF: максимум 5 МБ и 20 мегапикселей.
Содержимое проверяется Pillow; расширение и Content-Type клиента не считаются
доказательством формата. Пустой файл возвращает 400, слишком большой — 413,
неподдерживаемое или повреждённое изображение — 415.
Фото отсутствующего товара или отсутствующее фото возвращает 404.

В Swagger авторизуйтесь, откройте `POST /api/admin/products/upload`, нажмите
**Try it out**, заполните поля и выберите локальный файл в поле `file`.
Вызов GET фотографии не требует токена.
Для React на отдельном origin добавьте origin backend перед относительным
`image_url`, например `http://127.0.0.1:8000/api/products/1/image`.
Текущий frontend уже делает это через `resolveProductImageUrl` из API-клиента.
В формах создания и редактирования товара доступны Image URL и выбор локального
файла с предпросмотром. Выбранный файл используется вместо ссылки.
Можно создать товар без фото, заменить существующее фото
или удалить его кнопкой **Remove photo** и сохранить изменения.

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
Тесты фото дополнительно проверяют байты файла в БД, публичную отдачу,
замену и удаление, ограничения размера/формата, Swagger file picker и обновление
существующей таблицы без потери товаров.
Тесты категорий проверяют перенос старых записей в `other`, повторный и частично
выполненный перенос, сохранение фото, пять фильтров и пагинацию после фильтрации,
обязательную категорию при создании, PATCH и multipart-валидацию, ограничения БД.

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
│   ├── test_api.py
│   ├── test_categories.py
│   └── test_images.py
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
        ├── images.py
        └── products.py
```

Новые пакеты заменяют пустые заготовки `app/models.py`, `app/schemas.py`
и `app/auth.py`. Alembic не используется.
