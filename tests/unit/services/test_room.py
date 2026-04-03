"""
Unit-тесты сервиса управления комнатами.

Тестируются: get_room_by_id, get_all_rooms, get_active_rooms, create_room, update_room, delete_room
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.room import (
    get_room_by_id, get_all_rooms, get_active_rooms, create_room, update_room, delete_room,
)
from src.schemas.Room import RoomCreate, RoomResponse, RoomUpdate
from src.services.exceptions import RoomNotFoundError


class TestGetRoomById:
    """Тесты функции get_room_by_id."""

    @pytest.mark.asyncio
    async def test_get_room_success(self, mock_room_repo, mock_room_model):
        """Тест успешного получения комнаты."""
        mock_room_repo.get_by_id.return_value = mock_room_model

        response = await get_room_by_id(mock_room_repo, 1)

        assert isinstance(response, RoomResponse)
        assert response.id == 1
        assert response.name == "Тестовая Комната"
        assert response.capacity == 5

    @pytest.mark.asyncio
    async def test_get_room_not_found(self, mock_room_repo):
        """Тест когда комната не найдена."""
        mock_room_repo.get_by_id.return_value = None

        with pytest.raises(RoomNotFoundError) as exc_info:
            await get_room_by_id(mock_room_repo, 999)

        assert "999" in str(exc_info.value)


class TestGetAllRooms:
    """Тесты функции get_all_rooms."""

    @pytest.mark.asyncio
    async def test_get_all_rooms(self, mock_room_repo, mock_room_model):
        """Тест получения всех комнат."""
        mock_room_repo.get_all.return_value = [mock_room_model]

        result = await get_all_rooms(mock_room_repo, skip=0, limit=10)

        assert len(result) == 1
        assert result[0].name == "Тестовая Комната"

    @pytest.mark.asyncio
    async def test_get_all_rooms_empty(self, mock_room_repo):
        """Тест пустого списка."""
        mock_room_repo.get_all.return_value = []

        result = await get_all_rooms(mock_room_repo)

        assert result == []


class TestGetActiveRooms:
    """Тесты функции get_active_rooms."""

    @pytest.mark.asyncio
    async def test_get_active_rooms(self, mock_room_repo, mock_room_model):
        """Тест получения активных комнат."""
        mock_room_repo.get_active_rooms.return_value = [mock_room_model]

        result = await get_active_rooms(mock_room_repo)

        assert len(result) == 1
        assert result[0].is_active is True


class TestCreateRoom:
    """Тесты функции create_room."""

    @pytest.mark.asyncio
    async def test_create_room_success(self, mock_room_repo, room_create_data):
        """Тест успешного создания комнаты."""
        created_room = MagicMock()
        created_room.id = 1
        created_room.name = "Тестовая комната"
        created_room.capacity = 5
        created_room.is_active = True
        mock_room_repo.create_room.return_value = created_room

        response = await create_room(mock_room_repo, room_create_data)

        assert isinstance(response, RoomResponse)
        assert response.id == 1
        assert response.name == "Тестовая Комната"
        mock_room_repo.session.commit.assert_called_once()


class TestUpdateRoom:
    """Тесты функции update_room."""

    @pytest.mark.asyncio
    async def test_update_room_success(self, mock_room_repo, mock_room_model):
        """Тест успешного обновления."""
        mock_room_repo.get_by_id.return_value = mock_room_model

        updated_room = MagicMock()
        updated_room.id = 1
        updated_room.name = "Новое название"
        updated_room.capacity = 10
        updated_room.is_active = True
        mock_room_repo.update.return_value = updated_room

        update_data = RoomUpdate(name="Новое название", capacity=10)
        response = await update_room(mock_room_repo, 1, update_data)

        assert response.name == "Новое Название"
        assert response.capacity == 10

    @pytest.mark.asyncio
    async def test_update_room_not_found(self, mock_room_repo):
        """Тест обновления несуществующей комнаты."""
        mock_room_repo.get_by_id.return_value = None

        update_data = RoomUpdate(name="Новое")
        with pytest.raises(RoomNotFoundError):
            await update_room(mock_room_repo, 999, update_data)


class TestDeleteRoom:
    """Тесты функции delete_room."""

    @pytest.mark.asyncio
    async def test_delete_room_success(self, mock_room_repo, mock_room_model):
        """Тест успешного удаления."""
        mock_room_repo.get_by_id.return_value = mock_room_model

        await delete_room(mock_room_repo, 1)

        mock_room_repo.delete.assert_called_once_with(mock_room_model)
        mock_room_repo.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_room_not_found(self, mock_room_repo):
        """Тест удаления несуществующей комнаты."""
        mock_room_repo.get_by_id.return_value = None

        with pytest.raises(RoomNotFoundError):
            await delete_room(mock_room_repo, 999)
