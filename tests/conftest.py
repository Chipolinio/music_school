"""
Главный conftest для unit-тестов сервисного слоя.

Содержит:
- Фикстуры мок-репозиториев для всех сервисов
- Общие тестовые данные (схемы, пользователи, комнаты и т.д.)
- Утилиты для моков
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

# === Имты схем ===
from src.schemas.User import UserCreate, UserResponse, UserUpdate, UserRole
from src.schemas.Room import RoomCreate, RoomResponse, RoomUpdate
from src.schemas.LessonSlot import LessonSlotCreate, LessonSlotResponse, LessonSlotUpdate
from src.schemas.LessonBooking import LessonCreate, LessonResponse
from src.schemas.RehearsalBooking import RehearsalCreate, RehearsalResponse
from src.schemas.Notification import NotificationCreate, NotificationResponse
from src.models.User import UserRole as DBUserRole
from src.models.LessonBooking import Status as BookingStatus
from src.models.Notification import MessageType


# =============================================================================
# MOCK SESSION
# =============================================================================

@pytest.fixture
def mock_session():
    """Фикстура мок-сессии SQLAlchemy."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# =============================================================================
# MOCK REPOSITORIES
# =============================================================================

@pytest.fixture
def mock_user_repo(mock_session):
    """Создаёт мок UserRepository."""
    repo = AsyncMock()
    repo.session = mock_session
    repo.get_by_id = AsyncMock()
    repo.get_by_phone = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_user = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_room_repo(mock_session):
    """Создаёт мок RoomRepository."""
    repo = AsyncMock()
    repo.session = mock_session
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.get_active_rooms = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_room = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_lesson_slot_repo(mock_session):
    """Создаёт мок LessonSlotRepository."""
    repo = AsyncMock()
    repo.session = mock_session
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_slot = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.find_conflicts = AsyncMock(return_value=[])
    repo.find_teacher_conflicts = AsyncMock(return_value=[])
    repo.get_by_teacher = AsyncMock(return_value=[])
    repo.get_slot_with_bookings = AsyncMock()
    repo.find_room_lesson_conflicts = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_lesson_booking_repo(mock_session):
    """Создаёт мок LessonBookingRepository."""
    repo = AsyncMock()
    repo.session = mock_session
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_booking = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.get_student_bookings = AsyncMock(return_value=[])
    repo.get_student_active_bookings = AsyncMock(return_value=[])
    repo.count_bookings_for_slot = AsyncMock(return_value=0)
    repo.get_booking_with_slot = AsyncMock()
    repo.get_lesson_count_by_teacher = AsyncMock(return_value=[])
    repo.get_user_attendance_stats = AsyncMock(return_value={
        "total_lessons": 0, "booked": 0, "attended": 0,
    })
    repo.get_peak_hours = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_rehearsal_repo(mock_session):
    """Создаёт мок RehearsalRepository."""
    repo = AsyncMock()
    repo.session = mock_session
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_rehearsal = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.find_room_conflicts = AsyncMock(return_value=[])
    repo.find_student_conflicts = AsyncMock(return_value=[])
    repo.get_student_rehearsals = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_notification_repo(mock_session):
    """Создаёт мок NotificationRepository."""
    repo = AsyncMock()
    repo.session = mock_session
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.get_unread = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.create_notification = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.mark_all_as_read = AsyncMock()
    return repo


# =============================================================================
# TEST DATA: Схемы
# =============================================================================

@pytest.fixture
def user_create_data():
    """Тестовые данные для регистрации."""
    return UserCreate(
        phone="+79991234567",
        full_name="Иванов Иван",
        password="SecurePass123",
        role=UserRole.STUDENT,
    )


@pytest.fixture
def user_create_teacher_data():
    """Тестовые данные для регистрации преподавателя."""
    return UserCreate(
        phone="+79991234568",
        full_name="Петров Пётр",
        password="SecurePass123",
        role=UserRole.TEACHER,
    )


@pytest.fixture
def user_update_data():
    """Тестовые данные для обновления."""
    return UserUpdate(
        full_name="Иванов Иван Иванович",
        phone="+79991234567",
    )


@pytest.fixture
def room_create_data():
    """Тестовые данные для создания комнаты."""
    return RoomCreate(
        name="Тестовая Комната",
        capacity=5,
        is_active=True,
    )


@pytest.fixture
def room_update_data():
    """Тестовые данные для обновления комнаты."""
    return RoomUpdate(
        name="Новое название",
        capacity=10,
    )


@pytest.fixture
def lesson_slot_create_data():
    """Тестовые данные для создания слота."""
    now = datetime.now(timezone.utc)
    return LessonSlotCreate(
        teacher_id=2,
        room_id=1,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        max_participants=3,
    )


@pytest.fixture
def lesson_slot_update_data():
    """Тестовые данные для обновления слота."""
    now = datetime.now(timezone.utc)
    return LessonSlotUpdate(
        start_time=now + timedelta(hours=3),
        end_time=now + timedelta(hours=4),
    )


@pytest.fixture
def lesson_create_data():
    """Тестовые данные для бронирования урока."""
    return LessonCreate(
        slot_id=1,
        student_id=1,
    )


@pytest.fixture
def rehearsal_create_data():
    """Тестовые данные для бронирования репетиции."""
    now = datetime.now(timezone.utc)
    return RehearsalCreate(
        student_id=1,
        room_id=1,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
    )


@pytest.fixture
def notification_create_data():
    """Тестовые данные для создания уведомления."""
    return NotificationCreate(
        user_id=1,
        title="Тестовое уведомление",
        message="Тестовое сообщение",
        type="INFO",
        is_read=False,
    )


# =============================================================================
# TEST DATA: Моки моделей (ORM объекты)
# =============================================================================

@pytest.fixture
def mock_user_model():
    """Создаёт мок ORM-пользователя (студент)."""
    user = MagicMock()
    user.id = 1
    user.phone = "+79991234567"
    user.full_name = "Иванов Иван"
    user.role = DBUserRole.STUDENT
    user.is_active = True
    return user


@pytest.fixture
def mock_teacher_model():
    """Создаёт мок ORM-пользователя (преподаватель)."""
    user = MagicMock()
    user.id = 2
    user.phone = "+79991234568"
    user.full_name = "Петров Пётр"
    user.role = DBUserRole.TEACHER
    user.is_active = True
    return user


@pytest.fixture
def mock_admin_model():
    """Создаёт мок ORM-пользователя (админ)."""
    user = MagicMock()
    user.id = 3
    user.phone = "+79991234569"
    user.full_name = "Админ Админов"
    user.role = DBUserRole.ADMIN
    user.is_active = True
    return user


@pytest.fixture
def mock_room_model():
    """Создаёт мок ORM-комнаты."""
    room = MagicMock()
    room.id = 1
    room.name = "Тестовая комната"
    room.capacity = 5
    room.is_active = True
    return room


@pytest.fixture
def mock_slot_model():
    """Создаёт мок ORM-слота урока."""
    now = datetime.now(timezone.utc)
    slot = MagicMock()
    slot.id = 1
    slot.teacher_id = 2
    slot.room_id = 1
    slot.start_time = now + timedelta(hours=1)
    slot.end_time = now + timedelta(hours=2)
    slot.max_participants = 3
    return slot


@pytest.fixture
def mock_booking_model():
    """Создаёт мок ORM-бронирования урока."""
    booking = MagicMock()
    booking.id = 1
    booking.slot_id = 1
    booking.student_id = 1
    booking.status = BookingStatus.BOOKED
    booking.booked_at = datetime.now(timezone.utc)
    booking.slot = MagicMock()
    return booking


@pytest.fixture
def mock_rehearsal_model():
    """Создаёт мок ORM-бронирования репетиции."""
    now = datetime.now(timezone.utc)
    rehearsal = MagicMock()
    rehearsal.id = 1
    rehearsal.student_id = 1
    rehearsal.room_id = 1
    rehearsal.start_time = now + timedelta(hours=1)
    rehearsal.end_time = now + timedelta(hours=2)
    rehearsal.status = BookingStatus.BOOKED
    return rehearsal


@pytest.fixture
def mock_notification_model():
    """Создаёт мок ORM-уведомления."""
    notification = MagicMock()
    notification.id = 1
    notification.user_id = 1
    notification.title = "Тестовое уведомление"
    notification.message = "Тестовое сообщение"
    notification.type = MessageType.INFO
    notification.is_read = False
    notification.created_at = datetime.now(timezone.utc)
    return notification


# =============================================================================
# JWT TOKEN HELPERS
# =============================================================================

@pytest.fixture
def valid_token():
    """Возвращает валидный JWT-токен (моковый)."""
    return "mock_valid_jwt_token_string"


@pytest.fixture
def expired_token():
    """Возвращает «протухший» JWT-токен (моковый)."""
    return "mock_expired_jwt_token_string"
