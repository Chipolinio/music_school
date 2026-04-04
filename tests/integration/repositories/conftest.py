"""
Conftest для интеграционных тестов репозиториев.

Переиспользует фикстуры из tests/integration/conftest.py и добавляет
специфичные фикстуры для тестов репозиториев.
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from src.models.User import User, UserRole
from src.models.Room import Room
from src.models.LessonSlot import LessonSlot
from src.models.LessonBooking import LessonBooking, Status as BookingStatus
from src.models.RehearsalBooking import RehearsalBooking, Status as RehearsalStatus
from src.models.Notification import Notification, MessageType


def _unique_phone(suffix=""):
    """Генерирует уникальный номер телефона."""
    return f"+7999{uuid.uuid4().hex[:8]}{suffix}"


# =============================================================================
# FIXTURES ДЛЯ ТЕСТОВ РЕПОЗИТОРИЕВ
# =============================================================================

@pytest.fixture
async def student(session, user_repo):
    """Создаёт студента."""
    user = await user_repo.create_user(
        phone=_unique_phone("1"),
        full_name="Тестовый Студент",
        hashed_password="hash",
        role="STUDENT",
    )
    await session.flush()
    await session.refresh(user)
    return user


@pytest.fixture
async def teacher(session, user_repo):
    """Создаёт преподавателя."""
    user = await user_repo.create_user(
        phone=_unique_phone("2"),
        full_name="Тестовый Преподаватель",
        hashed_password="hash",
        role="TEACHER",
    )
    await session.flush()
    await session.refresh(user)
    return user


@pytest.fixture
async def admin(session, user_repo):
    """Создаёт админа."""
    user = await user_repo.create_user(
        phone=_unique_phone("3"),
        full_name="Тестовый Админ",
        hashed_password="hash",
        role="ADMIN",
    )
    await session.flush()
    await session.refresh(user)
    return user


@pytest.fixture
async def room(session, room_repo):
    """Создаёт комнату."""
    r = await room_repo.create_room(
        name="Тестовая комната",
        capacity=3,
        is_active=True,
    )
    await session.flush()
    await session.refresh(r)
    return r


@pytest.fixture
async def slot(session, lesson_slot_repo, teacher, room):
    """Создаёт слот урока."""
    now = datetime.now(timezone.utc)
    s = await lesson_slot_repo.create_slot(
        teacher_id=teacher.id,
        room_id=room.id,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        max_participants=3,
    )
    await session.flush()
    await session.refresh(s)
    return s


@pytest.fixture
async def booking(session, lesson_booking_repo, slot, student):
    """Создаёт бронирование урока."""
    b = await lesson_booking_repo.create_booking(
        slot_id=slot.id,
        student_id=student.id,
        status="BOOKED",
    )
    await session.flush()
    await session.refresh(b)
    return b
