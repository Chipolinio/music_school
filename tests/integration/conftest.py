"""
Conftest для интеграционных тестов сервисного слоя.

Использует тестовую БД (PostgreSQL) с реальными репозиториями
и автоматическим откатом транзакций после каждого теста.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from src.models.Base import BaseModel
from src.models.User import User, UserRole as DBUserRole
from src.models.Room import Room
from src.models.LessonSlot import LessonSlot
from src.models.LessonBooking import LessonBooking, Status as BookingStatus
from src.models.RehearsalBooking import RehearsalBooking, Status as RehearsalStatus
from src.models.Notification import Notification, MessageType

from src.repositories.UserRepository import UserRepository
from src.repositories.RoomRepository import RoomRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.LessonBookingRepository import LessonBookingRepository
from src.repositories.RehearsalBookingRepository import RehearsalRepository
from src.repositories.NotificationRepository import NotificationRepository

from src.utils.security import get_password_hash


# =============================================================================
# TEST DATABASE (PostgreSQL)
# =============================================================================

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5436/music_school_test_db"


def _unique_phone():
    """Генерирует уникальный номер телефона."""
    return f"+7999{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Использовать единый event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
async def engine():
    """Создаёт движок для тестовой БД."""
    engine = create_async_engine(TEST_DATABASE_URL)

    # Удаляем и создаём таблицы заново
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)

    yield engine

    # Удаляем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Создаёт сессию для каждого теста с автоматическим откатом."""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        # Откатываем все изменения после теста
        # (для repository tests — rollback, для service tests — тоже rollback если не было commit)
        try:
            await session.rollback()
        except Exception:
            pass  # Транзакция уже закрыта (например, после commit в service layer)


# =============================================================================
# REPOSITORIES С РЕАЛЬНОЙ СЕССИЕЙ
# =============================================================================

@pytest.fixture
def user_repo(session):
    """Реальный UserRepository с тестовой сессией."""
    return UserRepository(session)


@pytest.fixture
def room_repo(session):
    """Реальный RoomRepository с тестовой сессией."""
    return RoomRepository(session)


@pytest.fixture
def lesson_slot_repo(session):
    """Реальный LessonSlotRepository с тестовой сессией."""
    return LessonSlotRepository(session)


@pytest.fixture
def lesson_booking_repo(session):
    """Реальный LessonBookingRepository с тестовой сессией."""
    return LessonBookingRepository(session)


@pytest.fixture
def rehearsal_repo(session):
    """Реальный RehearsalRepository с тестовой сессией."""
    return RehearsalRepository(session)


@pytest.fixture
def notification_repo(session):
    """Реальный NotificationRepository с тестовой сессией."""
    return NotificationRepository(session)


# =============================================================================
# TEST DATA: Создание данных в БД
# =============================================================================

@pytest.fixture
async def test_student(session, user_repo):
    """Создаёт тестового студента."""
    created = await user_repo.create_user(
        phone=_unique_phone(),
        full_name="Тестовый Студент",
        hashed_password=get_password_hash("Password123"),
        role="STUDENT",
    )
    await session.flush()
    await session.refresh(created)
    return created


@pytest.fixture
async def test_teacher(session, user_repo):
    """Создаёт тестового преподавателя."""
    created = await user_repo.create_user(
        phone=_unique_phone(),
        full_name="Тестовый Преподаватель",
        hashed_password=get_password_hash("Password123"),
        role="TEACHER",
    )
    await session.flush()
    await session.refresh(created)
    return created


@pytest.fixture
async def test_admin(session, user_repo):
    """Создаёт тестового админа."""
    created = await user_repo.create_user(
        phone=_unique_phone(),
        full_name="Тестовый Админ",
        hashed_password=get_password_hash("Password123"),
        role="ADMIN",
    )
    await session.flush()
    await session.refresh(created)
    return created


@pytest.fixture
async def test_room(session, room_repo):
    """Создаёт тестовую комнату."""
    created = await room_repo.create_room(
        name="Тестовая комната",
        capacity=3,
        is_active=True,
    )
    await session.flush()
    await session.refresh(created)
    return created


@pytest.fixture
async def test_slot(session, lesson_slot_repo, test_teacher, test_room):
    """Создаёт тестовый слот урока."""
    now = datetime.now(timezone.utc)
    created = await lesson_slot_repo.create_slot(
        teacher_id=test_teacher.id,
        room_id=test_room.id,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        max_participants=3,
    )
    await session.flush()
    await session.refresh(created)
    return created


@pytest.fixture
async def test_booking(session, lesson_booking_repo, test_slot, test_student):
    """Создаёт тестовое бронирование урока."""
    created = await lesson_booking_repo.create_booking(
        slot_id=test_slot.id,
        student_id=test_student.id,
    )
    await session.flush()
    await session.refresh(created)
    return created


@pytest.fixture
async def test_notification(session, notification_repo, test_student):
    """Создаёт тестовое уведомление."""
    created = await notification_repo.create_notification(
        user_id=test_student.id,
        title="Тестовое уведомление",
        message="Тестовое сообщение",
        msg_type="INFO",
        is_read=False,
    )
    await session.flush()
    await session.refresh(created)
    return created
