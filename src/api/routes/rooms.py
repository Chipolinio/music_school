"""
API роуты для комнат.
"""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_room_service, RoomService
from src.schemas.Room import RoomResponse, RoomCreate, RoomUpdate, RoomListResponse, RoomCreateResponse, RoomUpdateResponse, RoomDeleteResponse


router = APIRouter(prefix="/rooms", tags=["Комнаты"])


@router.get("/active", response_model=RoomListResponse)
async def get_active_rooms(
    service: RoomService = Depends(get_room_service),
):
    """Получение активных комнат."""
    rooms = await service.get_active()
    return RoomListResponse(rooms=rooms, total=len(rooms))


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    service: RoomService = Depends(get_room_service),
):
    """Получение комнаты по ID."""
    return await service.get_by_id(room_id)


@router.get("/", response_model=RoomListResponse)
async def get_rooms(
    skip: int = 0,
    limit: int = 100,
    service: RoomService = Depends(get_room_service),
):
    """Получение всех комнат с пагинацией."""
    rooms = await service.get_all(skip=skip, limit=limit)
    return RoomListResponse(rooms=rooms, total=len(rooms))


@router.post("/", response_model=RoomCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    service: RoomService = Depends(get_room_service),
):
    """Создание новой комнаты."""
    room = await service.create(room_data)
    return RoomCreateResponse(room=room, message="Комната успешно создана")


@router.patch("/{room_id}", response_model=RoomUpdateResponse)
async def update_room(
    room_id: int,
    update_data: RoomUpdate,
    service: RoomService = Depends(get_room_service),
):
    """Обновление комнаты."""
    room = await service.update(room_id, update_data)
    return RoomUpdateResponse(room=room, message="Комната успешно обновлена")


@router.delete("/{room_id}", response_model=RoomDeleteResponse)
async def delete_room(
    room_id: int,
    service: RoomService = Depends(get_room_service),
):
    """Удаление комнаты."""
    await service.delete(room_id)
    return RoomDeleteResponse(message="Комната успешно удалена")
