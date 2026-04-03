"""
Сервис управления расписанием уроков.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import List

from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.UserRepository import UserRepository
from src.repositories.RoomRepository import RoomRepository
from src.schemas.LessonSlot import LessonSlotCreate, LessonSlotResponse, LessonSlotUpdate
from src.schemas.User import UserRole
from src.services.exceptions import (
    InvalidRoleError,
    UserNotFoundError,
    RoomNotFoundError,
    SlotNotFoundError,
    SlotConflictError,
)

logger = logging.getLogger(__name__)


def _validate_duration(start_time, end_time) -> None:
    """
    Проверяет длительность слота.

    Args:
        start_time: Время начала
        end_time: Время окончания

    Raises:
        ValueError: если длительность не соответствует требованиям
    """
    duration_minutes = (end_time - start_time).total_seconds() / 60
    if duration_minutes < 60:
        raise ValueError("Минимальная длительность слота — 1 час")
    if duration_minutes > 120:
        raise ValueError("Максимальная длительность слота — 2 часа")


async def create_slot(
    lesson_slot_repository: LessonSlotRepository,
    user_repository: UserRepository,
    room_repository: RoomRepository,
    slot_data: LessonSlotCreate,
    current_user_role: UserRole,
) -> LessonSlotResponse:
    """
    Создаёт слот урока.

    Args:
        lesson_slot_repository: Репозиторий слотов
        user_repository: Репозиторий пользователей
        room_repository: Репозиторий комнат
        slot_data: Данные слота для создания
        current_user_role: Роль текущего пользователя

    Returns:
        LessonSlotResponse: Данные созданного слота

    Raises:
        InvalidRoleError: если недостаточно прав
        UserNotFoundError: если преподаватель не найден
        RoomNotFoundError: если комната не найдена
        SlotConflictError: если обнаружен конфликт
    """
    logger.debug(f"Создание слота урока: преподаватель={slot_data.teacher_id}, комната={slot_data.room_id}")

    if current_user_role != UserRole.ADMIN:
        logger.warning(f"Пользователь с ролью {current_user_role} попытался создать слот")
        raise InvalidRoleError("Только ADMIN может создавать слоты уроков")

    teacher = await user_repository.get_by_id(slot_data.teacher_id)
    if teacher is None:
        logger.warning(f"Преподаватель с ID {slot_data.teacher_id} не найден")
        raise UserNotFoundError(user_id=slot_data.teacher_id)

    if teacher.role != "TEACHER":
        logger.warning(f"Пользователь {slot_data.teacher_id} не является преподавателем")
        raise InvalidRoleError("Преподаватель должен иметь роль TEACHER")

    room = await room_repository.get_by_id(slot_data.room_id)
    if room is None:
        logger.warning(f"Комната с ID {slot_data.room_id} не найдена")
        raise RoomNotFoundError(slot_data.room_id)

    _validate_duration(slot_data.start_time, slot_data.end_time)

    teacher_conflicts = await lesson_slot_repository.find_teacher_conflicts(
        teacher_id=slot_data.teacher_id,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
    )
    if teacher_conflicts:
        logger.warning(f"Обнаружен конфликт преподавателя {slot_data.teacher_id}")
        raise SlotConflictError(
            f"Преподаватель уже занят в указанное время (конфликтов: {len(teacher_conflicts)})"
        )

    room_conflicts = await lesson_slot_repository.find_conflicts(
        room_id=slot_data.room_id,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
    )
    if room_conflicts:
        logger.warning(f"Обнаружен конфликт комнаты {slot_data.room_id}")
        raise SlotConflictError(
            f"Комната уже занята в указанное время (конфликтов: {len(room_conflicts)})"
        )

    created_slot = await lesson_slot_repository.create_slot(
        teacher_id=slot_data.teacher_id,
        room_id=slot_data.room_id,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        max_participants=slot_data.max_participants,
    )
    await lesson_slot_repository.session.commit()
    logger.info(f"Слот урока {created_slot.id} успешно создан")

    return LessonSlotResponse(
        id=created_slot.id,
        teacher_id=created_slot.teacher_id,
        room_id=created_slot.room_id,
        start_time=created_slot.start_time,
        end_time=created_slot.end_time,
        max_participants=created_slot.max_participants,
    )


async def get_slot_by_id(
    lesson_slot_repository: LessonSlotRepository,
    slot_id: int,
) -> LessonSlotResponse:
    """
    Получает слот по ID.

    Args:
        lesson_slot_repository: Репозиторий слотов
        slot_id: ID слота

    Returns:
        LessonSlotResponse: Данные слота

    Raises:
        SlotNotFoundError: если слот не найден
    """
    logger.debug(f"Получение слота по ID: {slot_id}")

    slot = await lesson_slot_repository.get_by_id(slot_id)
    if slot is None:
        logger.warning(f"Слот с ID {slot_id} не найден")
        raise SlotNotFoundError(slot_id)

    return LessonSlotResponse(
        id=slot.id,
        teacher_id=slot.teacher_id,
        room_id=slot.room_id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        max_participants=slot.max_participants,
    )


async def get_all_slots(
    lesson_slot_repository: LessonSlotRepository,
    skip: int = 0,
    limit: int = 100,
) -> List[LessonSlotResponse]:
    """Получает все слоты с пагинацией."""
    logger.debug(f"Получение списка слотов: skip={skip}, limit={limit}")

    slots = await lesson_slot_repository.get_all(skip=skip, limit=limit)
    return [
        LessonSlotResponse(
            id=s.id,
            teacher_id=s.teacher_id,
            room_id=s.room_id,
            start_time=s.start_time,
            end_time=s.end_time,
            max_participants=s.max_participants,
        )
        for s in slots
    ]


async def get_teacher_slots(
    lesson_slot_repository: LessonSlotRepository,
    teacher_id: int,
) -> List[LessonSlotResponse]:
    """Получает все слоты конкретного преподавателя."""
    logger.debug(f"Получение слотов преподавателя {teacher_id}")

    slots = await lesson_slot_repository.get_by_teacher(teacher_id)
    return [
        LessonSlotResponse(
            id=s.id,
            teacher_id=s.teacher_id,
            room_id=s.room_id,
            start_time=s.start_time,
            end_time=s.end_time,
            max_participants=s.max_participants,
        )
        for s in slots
    ]


async def update_slot(
    lesson_slot_repository: LessonSlotRepository,
    user_repository: UserRepository,
    room_repository: RoomRepository,
    slot_id: int,
    update_data: LessonSlotUpdate,
    current_user_role: UserRole,
) -> LessonSlotResponse:
    """
    Обновляет слот.

    Args:
        lesson_slot_repository: Репозиторий слотов
        user_repository: Репозиторий пользователей
        room_repository: Репозиторий комнат
        slot_id: ID слота для обновления
        update_data: Данные для обновления
        current_user_role: Роль текущего пользователя

    Returns:
        LessonSlotResponse: Обновлённые данные слота

    Raises:
        InvalidRoleError: если недостаточно прав
        SlotNotFoundError: если слот не найден
        SlotConflictError: если обнаружен конфликт
    """
    logger.debug(f"Обновление слота {slot_id}")

    if current_user_role != UserRole.ADMIN:
        logger.warning(f"Пользователь с ролью {current_user_role} попытался обновить слот")
        raise InvalidRoleError("Только ADMIN может обновлять слоты уроков")

    slot = await lesson_slot_repository.get_by_id(slot_id)
    if slot is None:
        logger.warning(f"Слот с ID {slot_id} не найден для обновления")
        raise SlotNotFoundError(slot_id)

    update_dict = update_data.model_dump(exclude_unset=True)

    new_start_time = update_dict.get("start_time", slot.start_time)
    new_end_time = update_dict.get("end_time", slot.end_time)

    if "start_time" in update_dict or "end_time" in update_dict:
        _validate_duration(new_start_time, new_end_time)

        teacher_id = update_dict.get("teacher_id", slot.teacher_id)
        teacher_conflicts = await lesson_slot_repository.find_teacher_conflicts(
            teacher_id=teacher_id,
            start_time=new_start_time,
            end_time=new_end_time,
            exclude_slot_id=slot_id,
        )
        if teacher_conflicts:
            logger.warning(f"Обнаружен конфликт преподавателя {teacher_id}")
            raise SlotConflictError(
                f"Преподаватель уже занят в указанное время (конфликтов: {len(teacher_conflicts)})"
            )

        room_id = update_dict.get("room_id", slot.room_id)
        room_conflicts = await lesson_slot_repository.find_conflicts(
            room_id=room_id,
            start_time=new_start_time,
            end_time=new_end_time,
            exclude_slot_id=slot_id,
        )
        if room_conflicts:
            logger.warning(f"Обнаружен конфликт комнаты {room_id}")
            raise SlotConflictError(
                f"Комната уже занята в указанное время (конфликтов: {len(room_conflicts)})"
            )

    for field, value in update_dict.items():
        if value is not None:
            setattr(slot, field, value)

    updated_slot = await lesson_slot_repository.update(slot)
    await lesson_slot_repository.session.commit()
    logger.info(f"Слот урока {slot_id} успешно обновлён")

    return LessonSlotResponse(
        id=updated_slot.id,
        teacher_id=updated_slot.teacher_id,
        room_id=updated_slot.room_id,
        start_time=updated_slot.start_time,
        end_time=updated_slot.end_time,
        max_participants=updated_slot.max_participants,
    )


async def delete_slot(
    lesson_slot_repository: LessonSlotRepository,
    slot_id: int,
    current_user_role: UserRole,
) -> None:
    """
    Удаляет слот.

    Args:
        lesson_slot_repository: Репозиторий слотов
        slot_id: ID слота для удаления
        current_user_role: Роль текущего пользователя

    Raises:
        InvalidRoleError: если недостаточно прав
        SlotNotFoundError: если слот не найден
    """
    logger.debug(f"Удаление слота {slot_id}")

    if current_user_role != UserRole.ADMIN:
        logger.warning(f"Пользователь с ролью {current_user_role} попытался удалить слот")
        raise InvalidRoleError("Только ADMIN может удалять слоты уроков")

    slot = await lesson_slot_repository.get_by_id(slot_id)
    if slot is None:
        logger.warning(f"Слот с ID {slot_id} не найден для удаления")
        raise SlotNotFoundError(slot_id)

    await lesson_slot_repository.delete(slot)
    await lesson_slot_repository.session.commit()
    logger.info(f"Слот урока {slot_id} успешно удалён")
