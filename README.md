# Music School Management System

Информационная система для управления музыкальной школой — учёт учеников, преподавателей, расписания, бронирования уроков и репетиционных комнат, а также аналитика и отчёты.

## Возможности

- **Управление пользователями** — регистрация, авторизация, роли (STUDENT / TEACHER / ADMIN), активация/деактивация
- **Расписание** — создание и управление слотами уроков, привязка к преподавателю и комнате
- **Бронирование уроков** — запись студентов на уроки, отмена броней
- **Аренда репетиционных комнат** — самостоятельное бронирование комнат студентами
- **Уведомления** — автоматические уведомления при записи, отмене, подтверждении
- **Отчёты** — аналитика по преподавателям, посещаемости, популярным часам; экспорт в CSV

## Технологии

| Слой | Технологии |
|------|-----------|
| **Backend** | Python, FastAPI, SQLAlchemy (async), Pydantic v2 |
| **База данных** | PostgreSQL 15 (asyncpg) |
| **Миграции** | Alembic |
| **Аутентификация** | JWT (RS256), httpOnly Cookie, bcrypt |
| **Фронтенд** | Vanilla JS SPA (hash-based router), CSS3 |
| **Тесты** | pytest, pytest-asyncio, httpx |
| **Инфраструктура** | Docker Compose |

## Архитектура

Проект следует слоистой архитектуре:

```
API Routes → Dependency Layer → Service Layer → Repository Layer → Database
```

- **Routes** (`src/api/routes/`) — HTTP-эндпоинты
- **Deps** (`src/api/deps.py`) — фабрики сервисов, зависимости авторизации
- **Services** (`src/services/`) — бизнес-логика (чистые функции)
- **Repositories** (`src/repositories/`) — доступ к данным
- **Models** (`src/models/`) — SQLAlchemy ORM
- **Schemas** (`src/schemas/`) — Pydantic request/response
- **Utils** (`src/utils/`) — JWT, хеширование паролей, валидаторы

## Структура проекта

```
├── alembic/                 # Миграции БД
├── jwt_tokens/              # RSA ключи для JWT
├── scripts/                 # Скрипты автоматизации
│   └── create_admin.py      # Создание первого администратора
├── src/
│   ├── api/                 # API роуты, deps, error handler
│   ├── core/                # Настройка async engine
│   ├── models/              # SQLAlchemy модели
│   ├── repositories/        # Репозитории (data access)
│   ├── schemas/             # Pydantic схемы
│   ├── services/            # Бизнес-логика
│   ├── static/              # Фронтенд SPA (HTML/CSS/JS)
│   ├── utils/               # JWT, пароль, валидаторы
│   └── main.py              # Точка входа FastAPI
├── tests/                   # Unit + Integration тесты
├── docker-compose.yml       # Docker Compose (PostgreSQL + приложение)
├── Dockerfile               # Образ приложения
├── requirements.txt         # Зависимости
├── settings.py              # Pydantic настройки
└── alembic.ini              # Конфигурация Alembic
```

## Запуск проекта

### 1. Клонирование репозитория

```bash
git clone git@github.com:Chipolinio/music_school.git
cd music_school
```

### 2. Создание .env файла

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Или создайте вручную:

```env
POSTGRES_DB=music_school_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5435
```

> **Примечание:** при запуске через `docker compose` значения `POSTGRES_HOST` и `POSTGRES_PORT` переопределяются внутри контейнеров автоматически (`postgres:5432`).

### 3. Запуск через Docker Compose

```bash
docker compose up -d --build
```

Флаг `-d` запускает контейнеры в фоновом режиме. Без него процесс займёт терминал, и при `Ctrl+C` всё остановится.

Что произойдёт:
1. Docker соберёт образ приложения (установит зависимости из `requirements.txt`)
2. Поднимется PostgreSQL контейнер (данные хранятся в Docker volume `music_school_postgres_data`)
3. Применятся Alembic миграции
4. Запустится FastAPI приложение на порту **8000**

Откройте **http://127.0.0.1:8000/** — фронтенд SPA, или **http://127.0.0.1:8000/docs** — Swagger API.

Остановка: `docker compose down`

Просмотр логов: `docker compose logs -f`

### Локальная разработка (без Docker для приложения)

Если хотите запускать приложение локально (например для отладки), а БД в Docker:

```bash
# 1. Запустить только БД
docker compose up -d postgres

# 2. Применить миграции
alembic upgrade head

# 3. Запустить приложение
uvicorn src.main:app --reload
```

Приложение будет доступно на **http://127.0.0.1:8000/**

## Первый администратор

При запуске проекта автоматически создаётся пользователь с ролью ADMIN. Данные по умолчанию:

| Поле | Значение |
|------|----------|
| Телефон | `+79991234567` |
| ФИО | `Администратор` |
| Пароль | `admin123456` |

Для изменения данных откройте файл `scripts/create_admin.py` и отредактируйте константы в начале файла:

```python
ADMIN_PHONE = "+79991234567"
ADMIN_FULL_NAME = "Администратор"
ADMIN_PASSWORD = "admin123456"
```

Скрипт запускается автоматически при `docker compose up --build` **после применения миграций**. Если администратор уже существует — создание пропускается.

## Миграция данных с другой машины

Если нужно перенести существующую базу данных:

1. **На старой машине создайте дамп:**
   ```bash
   pg_dump -h localhost -p 5435 -U postgres music_school_db > backup.sql
   ```

2. **На новой машине запустите только БД:**
   ```bash
   docker compose up -d postgres
   ```

3. **Скопируйте и восстановите дамп:**
   ```bash
   docker cp backup.sql music_school_db:/backup.sql
   docker exec music_school_db psql -U postgres -d music_school_db -f /backup.sql
   ```

4. **Запустите весь проект:**
   ```bash
   docker compose up --build
   ```

## API Endpoints

| Группа | Префикс | Описание |
|--------|---------|----------|
| Auth | `/auth` | Регистрация, вход, выход, проверка токена |
| Users | `/users` | Управление пользователями |
| Rooms | `/rooms` | Управление комнатами |
| Schedule | `/schedule` | Расписание уроков |
| Bookings | `/bookings` | Бронирование уроков |
| Rehearsals | `/rehearsals` | Бронирование репетиций |
| Notifications | `/notifications` | Уведомления |
| Reports | `/reports` | Отчёты и CSV-экспорт |

## Аутентификация

- JWT (RS256) в **httpOnly Cookie** — фронтенд не имеет доступа к токену
- Время жизни токена: 30 минут
- Автоматическая отправка cookie при каждом запросе (`credentials: 'include'`)

## Роли

| Роль | Доступ |
|------|--------|
| **STUDENT** | Запись на уроки, аренда комнат, просмотр своих записей |
| **TEACHER** | Просмотр своего расписания |
| **ADMIN** | Полный доступ: управление пользователями, комнатами, расписанием, отчёты |

## Тестирование

```bash
# Unit-тесты
pytest tests/unit/

# Integration-тесты (нужен запущенный test DB на порту 5436)
docker compose up -d postgres_test
pytest tests/integration/

# Все тесты
pytest
```

## Фронтенд

SPA на чистом JavaScript без фреймворков:
- Hash-based маршрутизация (`#home`, `#dashboard`, `#admin` и т.д.)
- Route guards по ролям
- Компоненты: навбар, модалки, toast-уведомления, уведомления с бейджем
- Адаптивная вёрстка (mobile-friendly)

## Конфигурация

Настройки через Pydantic Settings + `.env` файл. Ключевые переменные:

| Переменная | Описание |
|------------|----------|
| `POSTGRES_*` | Подключение к БД |
| `JWT_PRIVATE_KEY_PATH` | Путь к RSA приватному ключу |
| `JWT_PUBLIC_KEY_PATH` | Путь к RSA публичному ключу |
| `JWT_LIFETIME_SECONDS` | Время жизни токена (по умолчанию 1800)
