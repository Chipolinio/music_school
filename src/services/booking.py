"""
Сервис бронирования уроков.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.repositories.LessonBookingRepository import LessonBookingRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.UserRepository import UserRepository
from src.repositories.NotificationRepository import NotificationRepository
from src.schemas.LessonBooking import LessonCreate, LessonResponse
from src.schemas.User import UserRole
from src.models.LessonBooking import Status as BookingStatus
from src.models.Notification import MessageType
from src.services.exceptions import (
    UserNotFoundError,
    SlotNotFoundError,
    InvalidRoleError,
    CapacityExceededError,
    BookingConflictError,
    BookingNotFoundError,
)

logger = logging.getLogger(__name__)


async def _check_student_double_booking(
    lesson_booking_repository: LessonBookingRepository,
    student_id: int,
    slot_start: datetime,
    slot_end: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    """
    Проверяет, не забронирован ли уже студент на другое занятие в это время.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        student_id: ID студента
        slot_start: Время начала слота
        slot_end: Время окончания слота
        exclude_booking_id: ID брони для исключения

    Returns:
        bool: True, если есть конфликт
    """
    bookings = await lesson_booking_repository.get_student_active_bookings(student_id)

    for booking in bookings:
        if exclude_booking_id and booking.id == exclude_booking_id:
            continue

        slot = booking.slot
        if slot is None:
            continue

        has_conflict = (slot.start_time < slot_end) and (slot.end_time > slot_start)
        if has_conflict:
            logger.debug(
                f"Обнаружен конфликт бронирования для студента {student_id}: "
                f"бронь {booking.id}, слот {slot.id}"
            )
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


async def book_lesson(
    lesson_booking_repository: LessonBookingRepository,
    lesson_slot_repository: LessonSlotRepository,
    user_repository: UserRepository,
    notification_repository: NotificationRepository,
    booking_data: LessonCreate,
    current_user_id: int,
    current_user_role: UserRole,
) -> LessonResponse:
    """
    Записывает студента на урок.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        lesson_slot_repository: Репозиторий слотов
        user_repository: Репозиторий пользователей
        notification_repository: Репозиторий уведомлений
        booking_data: Данные бронирования
        current_user_id: ID текущего пользователя
        current_user_role: Роль текущего пользователя

    Returns:
        LessonResponse: Данные созданной брони

    Raises:
        UserNotFoundError: если студент не найден
        SlotNotFoundError: если слот не найден
        InvalidRoleError: если недостаточно прав
        CapacityExceededError: если слот заполнен
        BookingConflictError: если есть конфликт бронирования
    """
    logger.debug(
        f"Запись на урок: студент={booking_data.student_id}, слот={booking_data.slot_id}"
    )

    student = await user_repository.get_by_id(booking_data.student_id)
    if student is None:
        logger.warning(f"Студент с ID {booking_data.student_id} не найден")
        raise UserNotFoundError(user_id=booking_data.student_id)

    if current_user_role != UserRole.ADMIN:
        if booking_data.student_id != current_user_id:
            logger.warning(
                f"Пользователь {current_user_id} попытался записать другого студента"
            )
            raise InvalidRoleError("STUDENT может записывать только себя")

    slot = await lesson_slot_repository.get_by_id(booking_data.slot_id)
    if slot is None:
        logger.warning(f"Слот с ID {booking_data.slot_id} не найден")
        raise SlotNotFoundError(booking_data.slot_id)

    booking_count = await lesson_booking_repository.count_bookings_for_slot(
        booking_data.slot_id
    )
    logger.debug(f"Количество записей в слот {booking_data.slot_id}: {booking_count}")

    if booking_count >= slot.max_participants:
        logger.warning(
            f"Превышена вместимость слота {booking_data.slot_id}: "
            f"{booking_count} >= {slot.max_participants}"
        )
        raise CapacityExceededError(booking_data.slot_id, slot.max_participants)

    has_conflict = await _check_student_double_booking(
        lesson_booking_repository=lesson_booking_repository,
        student_id=booking_data.student_id,
        slot_start=slot.start_time,
        slot_end=slot.end_time,
    )
    if has_conflict:
        logger.warning(f"Обнаружен конфликт бронирования для студента {booking_data.student_id}")
        raise BookingConflictError(
            f"Студент уже записан на другое занятие в это время"
        )

    created_booking = await lesson_booking_repository.create_booking(
        slot_id=booking_data.slot_id,
        student_id=booking_data.student_id,
    )
    await lesson_booking_repository.session.commit()
    logger.info(f"Успешная запись на урок: бронь {created_booking.id}")

    await _create_notification(
        notification_repository=notification_repository,
        user_id=booking_data.student_id,
        title="Запись на урок подтверждена",
        message=f"Вы записаны на урок в слоте {slot.id}",
        msg_type=MessageType.BOOKING_CONFIRM,
    )

    return LessonResponse(
        id=created_booking.id,
        slot_id=created_booking.slot_id,
        student_id=created_booking.student_id,
        booked_at=created_booking.booked_at,
    )


async def get_booking_by_id(
    lesson_booking_repository: LessonBookingRepository,
    booking_id: int,
) -> LessonResponse:
    """
    Получает бронь по ID.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        booking_id: ID брони

    Returns:
        LessonResponse: Данные брони

    Raises:
        BookingNotFoundError: если бронь не найдена
    """
    logger.debug(f"Получение брони по ID: {booking_id}")

    booking = await lesson_booking_repository.get_booking_with_slot(booking_id)
    if booking is None:
        logger.warning(f"Бронь с ID {booking_id} не найдена")
        raise BookingNotFoundError(booking_id)

    return LessonResponse(
        id=booking.id,
        slot_id=booking.slot_id,
        student_id=booking.student_id,
        booked_at=booking.booked_at,
    )


async def get_student_bookings(
    lesson_booking_repository: LessonBookingRepository,
    student_id: int,
) -> List[LessonResponse]:
    """
    Получает все брони студента.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        student_id: ID студента

    Returns:
        List[LessonResponse]: Список броней
    """
    logger.debug(f"Получение броней студента {student_id}")

    bookings = await lesson_booking_repository.get_student_bookings(student_id)
    return [
        LessonResponse(
            id=b.id,
            slot_id=b.slot_id,
            student_id=b.student_id,
            booked_at=b.booked_at,
        )
        for b in bookings
    ]


async def cancel_booking(
    lesson_booking_repository: LessonBookingRepository,
    notification_repository: NotificationRepository,
    booking_id: int,
    current_user_id: int,
    current_user_role: UserRole,
) -> None:
    """
    Отменяет бронь.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        notification_repository: Репозиторий уведомлений
        booking_id: ID брони для отмены
        current_user_id: ID текущего пользователя
        current_user_role: Роль текущего пользователя

    Raises:
        BookingNotFoundError: если бронь не найдена
        InvalidRoleError: если недостаточно прав
    """
    logger.debug(f"Отмена брони {booking_id}")

    booking = await lesson_booking_repository.get_booking_with_slot(booking_id)
    if booking is None:
        logger.warning(f"Бронь с ID {booking_id} не найдена для отмены")
        raise BookingNotFoundError(booking_id)

    if current_user_role != UserRole.ADMIN:
        if booking.student_id != current_user_id:
            logger.warning(
                f"Пользователь {current_user_id} попытался отменить чужую бронь {booking_id}"
            )
            raise InvalidRoleError("STUDENT может отменять только свою бронь")

    booking.status = BookingStatus.FREE
    await lesson_booking_repository.update(booking)
    await lesson_booking_repository.session.commit()
    logger.info(f"Бронь {booking_id} успешно отменена")

    await _create_notification(
        notification_repository=notification_repository,
        user_id=booking.student_id,
        title="Бронь отменена",
        message=f"Ваша бронь на урок {booking.slot_id} отменена",
        msg_type=MessageType.CANCELLATION,
    )
