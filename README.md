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
| **Инфраструктура** | Docker Compose (PostgreSQL) |

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
├── docker-compose.yml       # PostgreSQL контейнеры
├── requirements.txt         # Зависимости
├── settings.py              # Pydantic настройки
└── alembic.ini              # Конфигурация Alembic
```

## Быстрый старт

### 1. Клонирование и подготовка

```bash
git clone git@github.com:Chipolinio/music_school.git
cd music_school
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Запуск PostgreSQL

```bash
docker compose up -d
```

### 3. Настройка .env

Создай `.env` на основе примера:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5435
POSTGRES_DB=music_school
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 4. Миграции

```bash
alembic upgrade head
```

### 5. Запуск сервера

```bash
uvicorn src.main:app --reload
```

### 6. Открыть в браузере

- **Фронтенд**: http://127.0.0.1:8000/
- **Swagger API**: http://127.0.0.1:8000/docs

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
| `JWT_LIFETIME_SECONDS` | Время жизни токена (по умолчанию 1800) |
