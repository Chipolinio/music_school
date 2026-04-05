"""
Фабрики сервисов и зависимости для API.

Инкапсулирует создание сервисов со всеми их зависимостями (репозиториями).
Роуты зависят только от этих фабрик, а не от репозиториев напрямую.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.repositories.UserRepository import UserRepository
from src.repositories.RoomRepository import RoomRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.LessonBookingRepository import LessonBookingRepository
from src.repositories.RehearsalBookingRepository import RehearsalRepository
from src.repositories.NotificationRepository import NotificationRepository

from src.services import auth as auth_service
from src.services import user as user_service
from src.services import room as room_service
from src.services import schedule as schedule_service
from src.services import booking as booking_service
from src.services import rehearsal as rehearsal_service
from src.services import notification as notification_service
from src.services import report as report_service

from src.schemas.User import UserRole
from src.utils.security import decode_token


# =============================================================================
# ФАБРИКИ СЕРВИСОВ
# =============================================================================

class AuthService:
    """Фабрика для Auth сервисов."""

    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def register(self, user_data):
        return await auth_service.register(self.user_repo, user_data)

    async def login(self, phone: str, password: str):
        return await auth_service.login(self.user_repo, phone, password)

    def logout(self, token: str):
        return auth_service.logout(token)

    def verify_token(self, token: str):
        return auth_service.verify_token_service(token)

    async def get_current_user(self, token: str):
        return await auth_service.get_current_user(self.user_repo, token)


class UserService:
    """Фабрика для User сервисов."""

    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def get_by_id(self, user_id: int):
        return await user_service.get_user_by_id(self.user_repo, user_id)

    async def get_all(self, skip: int, limit: int, role: Optional[UserRole] = None):
        return await user_service.get_all_users(self.user_repo, skip, limit, role)

    async def update(self, user_id: int, update_data, current_user_role: UserRole):
        return await user_service.update_user(self.user_repo, user_id, update_data, current_user_role)

    async def deactivate(self, user_id: int, current_user_role: UserRole):
        return await user_service.deactivate_user(self.user_repo, user_id, current_user_role)

    async def activate(self, user_id: int, current_user_role: UserRole):
        return await user_service.activate_user(self.user_repo, user_id, current_user_role)


class RoomService:
    """Фабрика для Room сервисов."""

    def __init__(self, session: AsyncSession):
        self.room_repo = RoomRepository(session)

    async def get_by_id(self, room_id: int):
        return await room_service.get_room_by_id(self.room_repo, room_id)

    async def get_all(self, skip: int, limit: int):
        return await room_service.get_all_rooms(self.room_repo, skip, limit)

    async def get_active(self):
        return await room_service.get_active_rooms(self.room_repo)

    async def create(self, room_data):
        return await room_service.create_room(self.room_repo, room_data)

    async def update(self, room_id: int, update_data):
        return await room_service.update_room(self.room_repo, room_id, update_data)

    async def delete(self, room_id: int):
        return await room_service.delete_room(self.room_repo, room_id)


class ScheduleService:
    """Фабрика для Schedule сервисов."""

    def __init__(self, session: AsyncSession):
        self.slot_repo = LessonSlotRepository(session)
        self.user_repo = UserRepository(session)
        self.room_repo = RoomRepository(session)

    async def create(self, slot_data, current_user_role: UserRole):
        return await schedule_service.create_slot(
            self.slot_repo, self.user_repo, self.room_repo, slot_data, current_user_role
        )

    async def get_by_id(self, slot_id: int):
        return await schedule_service.get_slot_by_id(self.slot_repo, slot_id)

    async def get_all(self, skip: int, limit: int):
        return await schedule_service.get_all_slots(self.slot_repo, skip, limit)

    async def get_teacher(self, teacher_id: int):
        return await schedule_service.get_teacher_slots(self.slot_repo, teacher_id)

    async def update(self, slot_id: int, update_data, current_user_role: UserRole):
        return await schedule_service.update_slot(
            self.slot_repo, self.user_repo, self.room_repo, slot_id, update_data, current_user_role
        )

    async def delete(self, slot_id: int, current_user_role: UserRole):
        return await schedule_service.delete_slot(self.slot_repo, slot_id, current_user_role)


class BookingService:
    """Фабрика для Booking сервисов."""

    def __init__(self, session: AsyncSession):
        self.booking_repo = LessonBookingRepository(session)
        self.slot_repo = LessonSlotRepository(session)
        self.user_repo = UserRepository(session)
        self.notification_repo = NotificationRepository(session)

    async def book(self, booking_data, current_user_id: int, current_user_role: UserRole):
        return await booking_service.book_lesson(
            self.booking_repo, self.slot_repo, self.user_repo, self.notification_repo,
            booking_data, current_user_id, current_user_role
        )

    async def get_by_id(self, booking_id: int):
        return await booking_service.get_booking_by_id(self.booking_repo, booking_id)

    async def get_student(self, student_id: int):
        return await booking_service.get_student_bookings(self.booking_repo, student_id)

    async def cancel(self, booking_id: int, current_user_id: int, current_user_role: UserRole):
        return await booking_service.cancel_booking(
            self.booking_repo, self.notification_repo,
            booking_id, current_user_id, current_user_role
        )


class RehearsalService:
    """Фабрика для Rehearsal сервисов."""

    def __init__(self, session: AsyncSession):
        self.rehearsal_repo = RehearsalRepository(session)
        self.slot_repo = LessonSlotRepository(session)
        self.room_repo = RoomRepository(session)
        self.user_repo = UserRepository(session)
        self.notification_repo = NotificationRepository(session)

    async def book(self, rehearsal_data, current_user_id: int, current_user_role: UserRole):
        return await rehearsal_service.book_rehearsal(
            self.rehearsal_repo, self.slot_repo, self.room_repo, self.user_repo, self.notification_repo,
            rehearsal_data, current_user_id, current_user_role
        )

    async def get_by_id(self, rehearsal_id: int):
        return await rehearsal_service.get_rehearsal_by_id(self.rehearsal_repo, rehearsal_id)

    async def get_student(self, student_id: int):
        return await rehearsal_service.get_student_rehearsals(self.rehearsal_repo, student_id)

    async def cancel(self, rehearsal_id: int, current_user_id: int, current_user_role: UserRole):
        return await rehearsal_service.cancel_rehearsal(
            self.rehearsal_repo, self.notification_repo,
            rehearsal_id, current_user_id, current_user_role
        )


class NotificationService:
    """Фабрика для Notification сервисов."""

    def __init__(self, session: AsyncSession):
        self.notification_repo = NotificationRepository(session)

    async def get_user(self, user_id: int, unread_only: bool = False):
        return await notification_service.get_user_notifications(
            self.notification_repo, user_id, unread_only
        )

    async def mark_as_read(self, notification_id: int, user_id: int):
        return await notification_service.mark_as_read(
            self.notification_repo, notification_id, user_id
        )

    async def mark_all_as_read(self, user_id: int):
        return await notification_service.mark_all_as_read(self.notification_repo, user_id)

    async def create(self, notification_data):
        return await notification_service.create_notification(
            self.notification_repo, notification_data
        )


class ReportService:
    """Фабрика для Report сервисов."""

    def __init__(self, session: AsyncSession):
        self.booking_repo = LessonBookingRepository(session)
        self.slot_repo = LessonSlotRepository(session)
        self.user_repo = UserRepository(session)

    async def get_lesson_count_by_teacher(self, start_date, end_date):
        return await report_service.get_lesson_count_by_teacher(
            self.booking_repo, self.user_repo, start_date, end_date
        )

    async def get_user_attendance(self, user_id: int, start_date, end_date):
        return await report_service.get_user_attendance(
            self.booking_repo, self.user_repo, user_id, start_date, end_date
        )

    async def get_peak_hours(self, start_date, end_date):
        return await report_service.get_peak_hours_report(
            self.booking_repo, start_date, end_date
        )

    async def export_lesson_count_csv(self, start_date, end_date):
        return await report_service.export_lesson_count_csv(
            self.booking_repo, self.user_repo, start_date, end_date
        )

    async def export_attendance_csv(self, user_id: int, start_date, end_date):
        return await report_service.export_attendance_csv(
            self.booking_repo, self.user_repo, user_id, start_date, end_date
        )

    async def export_peak_hours_csv(self, start_date, end_date):
        return await report_service.export_peak_hours_csv(
            self.booking_repo, start_date, end_date
        )


# =============================================================================
# DEPENDS-ФАБРИКИ
# =============================================================================

def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Зависимость для получения AuthService."""
    return AuthService(session)


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    """Зависимость для получения UserService."""
    return UserService(session)


def get_room_service(session: AsyncSession = Depends(get_session)) -> RoomService:
    """Зависимость для получения RoomService."""
    return RoomService(session)


def get_schedule_service(session: AsyncSession = Depends(get_session)) -> ScheduleService:
    """Зависимость для получения ScheduleService."""
    return ScheduleService(session)


def get_booking_service(session: AsyncSession = Depends(get_session)) -> BookingService:
    """Зависимость для получения BookingService."""
    return BookingService(session)


def get_rehearsal_service(session: AsyncSession = Depends(get_session)) -> RehearsalService:
    """Зависимость для получения RehearsalService."""
    return RehearsalService(session)


def get_notification_service(session: AsyncSession = Depends(get_session)) -> NotificationService:
    """Зависимость для получения NotificationService."""
    return NotificationService(session)


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    """Зависимость для получения ReportService."""
    return ReportService(session)


# =============================================================================
# ЗАВИСИМОСТИ ДЛЯ ПРОВЕРКИ АВТОРИЗАЦИИ
# =============================================================================

async def get_current_user_from_request(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Извлекает данные текущего пользователя из cookies.

    Добавляет в request.state:
    - current_user_id: int
    - current_user_role: str
    - current_user: UserResponse
    """
    token = request.cookies.get("jwt_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = auth_service.verify_token(token)
        user_id = int(payload.get("sub"))
        role = payload.get("role")

        user = await auth_service.get_current_user(token)

        request.state.current_user_id = user_id
        request.state.current_user_role = role
        request.state.current_user = user

        return {
            "user_id": user_id,
            "role": role,
            "user": user,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(user_data: dict = Depends(get_current_user_from_request)):
    """Проверяет, что пользователь имеет роль ADMIN."""
    if user_data["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль ADMIN",
        )
    return user_data
