"""
Сервис бронирования репетиций.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.repositories.RehearsalBookingRepository import RehearsalRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.RoomRepository import RoomRepository
from src.repositories.UserRepository import UserRepository
from src.repositories.NotificationRepository import NotificationRepository
from src.schemas.RehearsalBooking import RehearsalCreate, RehearsalResponse
from src.schemas.User import UserRole
from src.models.RehearsalBooking import Status as BookingStatus
from src.models.Notification import MessageType
from src.services.exceptions import (
    UserNotFoundError,
    RoomNotFoundError,
    InvalidRoleError,
    BookingConflictError,
    BookingNotFoundError,
)

logger = logging.getLogger(__name__)


async def _check_room_conflict(
    rehearsal_repository: RehearsalRepository,
    lesson_slot_repository: LessonSlotRepository,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    """
    Проверяет конфликты комнаты с другими репетициями и уроками.

    Args:
        rehearsal_repository: Репозиторий репетиций
        lesson_slot_repository: Репозиторий слотов уроков
        room_id: ID комнаты
        start_time: Время начала
        end_time: Время окончания
        exclude_booking_id: ID брони для исключения

    Returns:
        bool: True, если есть конфликт
    """
    room_conflicts = await rehearsal_repository.find_room_conflicts(
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        exclude_booking_id=exclude_booking_id,
    )
    if room_conflicts:
        logger.debug(f"Обнаружен конфликт комнаты {room_id} с репетициями")
        return True

    lesson_conflicts = await lesson_slot_repository.find_room_lesson_conflicts(
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )
    if lesson_conflicts:
        logger.debug(f"Обнаружен конфликт комнаты {room_id} с уроками")
        return True

    return False


async def _check_student_double_booking(
    rehearsal_repository: RehearsalRepository,
    student_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    """
    Проверяет, не забронировал ли студент другую комнату на пересекающееся время.

    Args:
        rehearsal_repository: Репозиторий репетиций
        student_id: ID студента
        start_time: Время начала
        end_time: Время окончания
        exclude_booking_id: ID брони для исключения

    Returns:
        bool: True, если есть конфликт
    """
    conflicts = await rehearsal_repository.find_student_conflicts(
        student_id=student_id,
        start_time=start_time,
        end_time=end_time,
        exclude_booking_id=exclude_booking_id,
    )
    if conflicts:
        logger.debug(f"Обнаружен конфликт студента {student_id}")
        return True
    return False


async def _create_notification(
    notification_repository: NotificationRepository,
    user_id: int,
    title: str,
    message: str,
    msg_type: MessageType,
) -> None:
    """
    Создаёт уведомление через NotificationRepository.
    """
    await notification_repository.create_notification(
        user_id=user_id,
        title=title,
        message=message,
        msg_type=msg_type.value,
    )
    await notification_repository.session.commit()


async def book_rehearsal(
    rehearsal_repository: RehearsalRepository,
    lesson_slot_repository: LessonSlotRepository,
    room_repository: RoomRepository,
    user_repository: UserRepository,
    notification_repository: NotificationRepository,
    rehearsal_data: RehearsalCreate,
    current_user_id: int,
    current_user_role: UserRole,
) -> RehearsalResponse:
    """
    Бронирует комнату для репетиции.

    Args:
        rehearsal_repository: Репозиторий репетиций
        lesson_slot_repository: Репозиторий слотов
        user_repository: Репозиторий пользователей
        notification_repository: Репозиторий уведомлений
        rehearsal_data: Данные бронирования
        current_user_id: ID текущего пользователя
        current_user_role: Роль текущего пользователя

    Returns:
        RehearsalResponse: Данные созданной брони

    Raises:
        UserNotFoundError: если студент не найден
        RoomNotFoundError: если комната не найдена
        InvalidRoleError: если недостаточно прав
        BookingConflictError: если есть конфликт
    """
    logger.debug(
        f"Бронирование репетиции: студент={rehearsal_data.student_id}, "
        f"комната={rehearsal_data.room_id}"
    )

    student = await user_repository.get_by_id(rehearsal_data.student_id)
    if student is None:
        logger.warning(f"Студент с ID {rehearsal_data.student_id} не найден")
        raise UserNotFoundError(user_id=rehearsal_data.student_id)

    if current_user_role != UserRole.ADMIN:
        if rehearsal_data.student_id != current_user_id:
            logger.warning(
                f"Пользователь {current_user_id} попытался забронировать репетицию для другого студента"
            )
            raise InvalidRoleError("STUDENT может бронировать только себя")

    room = await room_repository.get_by_id(rehearsal_data.room_id)
    if room is None:
        logger.warning(f"Комната с ID {rehearsal_data.room_id} не найдена")
        raise RoomNotFoundError(rehearsal_data.room_id)

    has_room_conflict = await _check_room_conflict(
        rehearsal_repository=rehearsal_repository,
        lesson_slot_repository=lesson_slot_repository,
        room_id=rehearsal_data.room_id,
        start_time=rehearsal_data.start_time,
        end_time=rehearsal_data.end_time,
    )
    if has_room_conflict:
        logger.warning(f"Обнаружен конфликт комнаты {rehearsal_data.room_id}")
        raise BookingConflictError(
            f"Комната уже занята в указанное время"
        )

    has_student_conflict = await _check_student_double_booking(
        rehearsal_repository=rehearsal_repository,
        student_id=rehearsal_data.student_id,
        start_time=rehearsal_data.start_time,
        end_time=rehearsal_data.end_time,
    )
    if has_student_conflict:
        logger.warning(f"Обнаружен конфликт студента {rehearsal_data.student_id}")
        raise BookingConflictError(
            f"Студент уже забронировал другую комнату на это время"
        )

    created_booking = await rehearsal_repository.create_rehearsal(
        student_id=rehearsal_data.student_id,
        room_id=rehearsal_data.room_id,
        start_time=rehearsal_data.start_time,
        end_time=rehearsal_data.end_time,
    )
    await rehearsal_repository.session.commit()
    logger.info(f"Репетиция {created_booking.id} успешно забронирована")

    await _create_notification(
        notification_repository=notification_repository,
        user_id=rehearsal_data.student_id,
        title="Репетиция подтверждена",
        message=f"Вы забронировали комнату {rehearsal_data.room_id}",
        msg_type=MessageType.BOOKING_CONFIRM,
    )

    return RehearsalResponse(
        id=created_booking.id,
        student_id=created_booking.student_id,
        room_id=created_booking.room_id,
        start_time=created_booking.start_time,
        end_time=created_booking.end_time,
        status=created_booking.status.value if hasattr(created_booking.status, 'value') else str(created_booking.status),
    )


async def get_rehearsal_by_id(
    rehearsal_repository: RehearsalRepository,
    rehearsal_id: int,
) -> RehearsalResponse:
    """
    Получает бронь репетиции по ID.

    Args:
        rehearsal_repository: Репозиторий репетиций
        rehearsal_id: ID брони

    Returns:
        RehearsalResponse: Данные брони

    Raises:
        BookingNotFoundError: если бронь не найдена
    """
    logger.debug(f"Получение репетиции по ID: {rehearsal_id}")

    booking = await rehearsal_repository.get_by_id(rehearsal_id)
    if booking is None:
        logger.warning(f"Репетиция с ID {rehearsal_id} не найдена")
        raise BookingNotFoundError(rehearsal_id)

    return RehearsalResponse(
        id=booking.id,
        student_id=booking.student_id,
        room_id=booking.room_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
    )


async def get_student_rehearsals(
    rehearsal_repository: RehearsalRepository,
    student_id: int,
) -> List[RehearsalResponse]:
    """
    Получает все репетиции студента.

    Args:
        rehearsal_repository: Репозиторий репетиций
        student_id: ID студента

    Returns:
        List[RehearsalResponse]: Список репетиций
    """
    logger.debug(f"Получение репетиций студента {student_id}")

    bookings = await rehearsal_repository.get_student_rehearsals(student_id)
    return [
        RehearsalResponse(
            id=b.id,
            student_id=b.student_id,
            room_id=b.room_id,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status.value if hasattr(b.status, 'value') else str(b.status),
        )
        for b in bookings
    ]


async def cancel_rehearsal(
    rehearsal_repository: RehearsalRepository,
    notification_repository: NotificationRepository,
    rehearsal_id: int,
    current_user_id: int,
    current_user_role: UserRole,
) -> None:
    """
    Отменяет репетицию.

    Args:
        rehearsal_repository: Репозиторий репетиций
        notification_repository: Репозиторий уведомлений
        rehearsal_id: ID брони для отмены
        current_user_id: ID текущего пользователя
        current_user_role: Роль текущего пользователя

    Raises:
        BookingNotFoundError: если бронь не найдена
        InvalidRoleError: если недостаточно прав
    """
    logger.debug(f"Отмена репетиции {rehearsal_id}")

    booking = await rehearsal_repository.get_by_id(rehearsal_id)
    if booking is None:
        logger.warning(f"Репетиция с ID {rehearsal_id} не найдена для отмены")
        raise BookingNotFoundError(rehearsal_id)

    if current_user_role != UserRole.ADMIN:
        if booking.student_id != current_user_id:
            logger.warning(
                f"Пользователь {current_user_id} попытался отменить чужую репетицию {rehearsal_id}"
            )
            raise InvalidRoleError("STUDENT может отменять только свою бронь")

    booking.status = BookingStatus.FREE
    await rehearsal_repository.update(booking)
    await rehearsal_repository.session.commit()
    logger.info(f"Репетиция {rehearsal_id} успешно отменена")

    await _create_notification(
        notification_repository=notification_repository,
        user_id=booking.student_id,
        title="Репетиция отменена",
        message=f"Ваша репетиция в комнате {booking.room_id} отменена",
        msg_type=MessageType.CANCELLATION,
    )
