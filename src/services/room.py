"""
Сервис управления комнатами.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import List

from src.repositories.RoomRepository import RoomRepository
from src.schemas.Room import RoomCreate, RoomResponse, RoomUpdate
from src.services.exceptions import RoomNotFoundError

logger = logging.getLogger(__name__)


async def get_room_by_id(
    room_repository: RoomRepository,
    room_id: int,
) -> RoomResponse:
    """
    Получает комнату по ID.

    Args:
        room_repository: Репозиторий комнат
        room_id: ID комнаты

    Returns:
        RoomResponse: Данные комнаты

    Raises:
        RoomNotFoundError: если комната не найдена
    """
    logger.debug(f"Получение комнаты по ID: {room_id}")

    room = await room_repository.get_by_id(room_id)
    if room is None:
        logger.warning(f"Комната с ID {room_id} не найдена")
        raise RoomNotFoundError(room_id)

    return RoomResponse(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        is_active=room.is_active,
    )


async def get_all_rooms(
    room_repository: RoomRepository,
    skip: int = 0,
    limit: int = 100,
) -> List[RoomResponse]:
    """
    Получает все комнаты с пагинацией.

    Args:
        room_repository: Репозиторий комнат
        skip: Количество записей для пропуска
        limit: Максимальное количество записей

    Returns:
        List[RoomResponse]: Список комнат
    """
    logger.debug(f"Получение списка комнат: skip={skip}, limit={limit}")

    rooms = await room_repository.get_all(skip=skip, limit=limit)
    return [
        RoomResponse(
            id=r.id,
            name=r.name,
            capacity=r.capacity,
            is_active=r.is_active,
        )
        for r in rooms
    ]


async def get_active_rooms(
    room_repository: RoomRepository,
) -> List[RoomResponse]:
    """
    Получает только активные комнаты.

    Args:
        room_repository: Репозиторий комнат

    Returns:
        List[RoomResponse]: Список активных комнат
    """
    logger.debug("Получение активных комнат")

    rooms = await room_repository.get_active_rooms()
    return [
        RoomResponse(
            id=r.id,
            name=r.name,
            capacity=r.capacity,
            is_active=r.is_active,
        )
        for r in rooms
    ]


async def create_room(
    room_repository: RoomRepository,
    room_data: RoomCreate,
) -> RoomResponse:
    """
    Создаёт новую комнату.
    """
    logger.debug(f"Создание комнаты: {room_data.name}")

    created_room = await room_repository.create_room(
        name=room_data.name,
        capacity=room_data.capacity,
        is_active=room_data.is_active,
    )
    await room_repository.session.commit()
    logger.info(f"Комната {created_room.id} успешно создана")

    return RoomResponse(
        id=created_room.id,
        name=created_room.name,
        capacity=created_room.capacity,
        is_active=created_room.is_active,
    )


async def update_room(
    room_repository: RoomRepository,
    room_id: int,
    update_data: RoomUpdate,
) -> RoomResponse:
    """
    Обновляет данные комнаты.
    """
    logger.debug(f"Обновление комнаты {room_id}")

    room = await room_repository.get_by_id(room_id)
    if room is None:
        logger.warning(f"Комната с ID {room_id} не найдена для обновления")
        raise RoomNotFoundError(room_id)

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(room, field, value)

    updated_room = await room_repository.update(room)
    await room_repository.session.commit()
    logger.info(f"Комната {room_id} успешно обновлена")

    return RoomResponse(
        id=updated_room.id,
        name=updated_room.name,
        capacity=updated_room.capacity,
        is_active=updated_room.is_active,
    )


async def delete_room(
    room_repository: RoomRepository,
    room_id: int,
) -> None:
    """
    Удаляет комнату.
    """
    logger.debug(f"Удаление комнаты {room_id}")

    room = await room_repository.get_by_id(room_id)
    if room is None:
        logger.warning(f"Комната с ID {room_id} не найдена для удаления")
        raise RoomNotFoundError(room_id)

    await room_repository.delete(room)
    await room_repository.session.commit()
    logger.info(f"Комната {room_id} успешно удалена")
