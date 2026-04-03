"""
Сервис аналитики и отчётов.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
import csv
import io
from datetime import date
from typing import List, Dict, Any

from src.repositories.LessonBookingRepository import LessonBookingRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.RehearsalBookingRepository import RehearsalRepository
from src.repositories.UserRepository import UserRepository
from src.services.exceptions import UserNotFoundError

logger = logging.getLogger(__name__)


async def get_lesson_count_by_teacher(
    lesson_booking_repository: LessonBookingRepository,
    user_repository: UserRepository,
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """
    Считает количество уроков по преподавателям за период.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        user_repository: Репозиторий пользователей
        start_date: Дата начала периода
        end_date: Дата окончания периода

    Returns:
        List[Dict[str, Any]]: Список словарей с данными
    """
    logger.debug(f"Генерация отчёта по урокам преподавателей: {start_date} - {end_date}")

    data = await lesson_booking_repository.get_lesson_count_by_teacher(start_date, end_date)

    result = []
    for item in data:
        teacher = await user_repository.get_by_id(item["teacher_id"])
        teacher_name = teacher.full_name if teacher else "Неизвестно"
        result.append({
            "teacher_id": item["teacher_id"],
            "teacher_name": teacher_name,
            "lesson_count": item["lesson_count"],
        })

    logger.info(f"Отчёт по урокам преподавателей: {len(result)} записей")
    return result


async def get_user_attendance(
    lesson_booking_repository: LessonBookingRepository,
    user_repository: UserRepository,
    user_id: int,
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """
    Считает посещаемость пользователя за период.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        user_repository: Репозиторий пользователей
        user_id: ID пользователя
        start_date: Дата начала периода
        end_date: Дата окончания периода

    Returns:
        Dict[str, Any]: Статистика посещаемости

    Raises:
        UserNotFoundError: если пользователь не найден
    """
    logger.debug(f"Генерация отчёта по посещаемости пользователя {user_id}")

    user = await user_repository.get_by_id(user_id)
    if user is None:
        logger.warning(f"Пользователь с ID {user_id} не найден")
        raise UserNotFoundError(user_id=user_id)

    stats = await lesson_booking_repository.get_user_attendance_stats(user_id, start_date, end_date)

    result = {
        "user_id": user_id,
        "user_name": user.full_name,
        "period": f"{start_date} - {end_date}",
        "total_lessons": stats["total_lessons"],
        "booked": stats["booked"],
        "attended": stats["attended"],
    }

    logger.info(f"Отчёт по посещаемости пользователя {user_id} готов")
    return result


async def get_peak_hours_report(
    lesson_booking_repository: LessonBookingRepository,
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """
    Определяет популярные часы для уроков.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        start_date: Дата начала периода
        end_date: Дата окончания периода

    Returns:
        List[Dict[str, Any]]: Список популярных часов
    """
    logger.debug(f"Генерация отчёта по популярным часам: {start_date} - {end_date}")

    data = await lesson_booking_repository.get_peak_hours(start_date, end_date)

    logger.info(f"Отчёт по популярным часам: {len(data)} записей")
    return data


def generate_csv(data: List[Dict[str, Any]], filename: str = "report") -> str:
    """
    Генерирует CSV-строку из списка словарей.

    Args:
        data: Список словарей с данными
        filename: Имя файла (для заголовка, опционально)

    Returns:
        str: CSV как строка
    """
    if not data:
        return ""

    output = io.StringIO()
    fieldnames = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


async def export_lesson_count_csv(
    lesson_booking_repository: LessonBookingRepository,
    user_repository: UserRepository,
    start_date: date,
    end_date: date,
) -> str:
    """
    Генерирует CSV-отчёт по урокам преподавателей.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        user_repository: Репозиторий пользователей
        start_date: Дата начала периода
        end_date: Дата окончания периода

    Returns:
        str: CSV-строка
    """
    data = await get_lesson_count_by_teacher(
        lesson_booking_repository, user_repository, start_date, end_date
    )
    return generate_csv(data)


async def export_attendance_csv(
    lesson_booking_repository: LessonBookingRepository,
    user_repository: UserRepository,
    user_id: int,
    start_date: date,
    end_date: date,
) -> str:
    """
    Генерирует CSV-отчёт по посещаемости пользователя.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        user_repository: Репозиторий пользователей
        user_id: ID пользователя
        start_date: Дата начала периода
        end_date: Дата окончания периода

    Returns:
        str: CSV-строка
    """
    data = await get_user_attendance(
        lesson_booking_repository, user_repository, user_id, start_date, end_date
    )
    return generate_csv([data])


async def export_peak_hours_csv(
    lesson_booking_repository: LessonBookingRepository,
    start_date: date,
    end_date: date,
) -> str:
    """
    Генерирует CSV-отчёт по популярным часам.

    Args:
        lesson_booking_repository: Репозиторий бронирований
        start_date: Дата начала периода
        end_date: Дата окончания периода

    Returns:
        str: CSV-строка
    """
    data = await get_peak_hours_report(lesson_booking_repository, start_date, end_date)
    return generate_csv(data)
