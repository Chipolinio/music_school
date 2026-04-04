"""
Тесты для RoomRepository.

Покрывает методы: create_room, get_active_rooms.

Чеклист (раздел 5.3):
| Метод | Тест |
|-------|------|
| `create_room` | Создание |
| `get_active_rooms` | Есть активные / Нет активных |
"""

import pytest

from src.models.Room import Room
from src.repositories.RoomRepository import RoomRepository


class TestRoomRepositoryCreateRoom:
    """Тесты метода create_room."""

    @pytest.mark.asyncio
    async def test_create_room(self, session):
        """Тест создания комнаты."""
        repo = RoomRepository(session)

        room = await repo.create_room(name="Класс фортепиано", capacity=3, is_active=True)

        assert room.id is not None
        assert room.name == "Класс фортепиано"
        assert room.capacity == 3
        assert room.is_active is True

    @pytest.mark.asyncio
    async def test_create_room_returns_instance(self, session):
        """create_room возвращает тот же экземпляр с заполненным ID."""
        repo = RoomRepository(session)

        room = await repo.create_room(name="Комната 1", capacity=5, is_active=True)

        assert room.id is not None
        assert isinstance(room, Room)

    @pytest.mark.asyncio
    async def test_create_room_default_is_active(self, session):
        """Тест: комната создаётся активной по умолчанию."""
        repo = RoomRepository(session)

        room = await repo.create_room(name="Комната", capacity=2)

        assert room.is_active is True

    @pytest.mark.asyncio
    async def test_create_room_is_active_false(self, session):
        """Тест создания неактивной комнаты."""
        repo = RoomRepository(session)

        room = await repo.create_room(name="Неактивная", capacity=2, is_active=False)

        assert room.is_active is False

    @pytest.mark.asyncio
    async def test_create_multiple_rooms(self, session):
        """Тест создания нескольких комнат."""
        repo = RoomRepository(session)

        room1 = await repo.create_room(name="Комната 1", capacity=3, is_active=True)
        room2 = await repo.create_room(name="Комната 2", capacity=5, is_active=True)

        assert room1.id is not None
        assert room2.id is not None
        assert room1.id != room2.id


class TestRoomRepositoryGetActiveRooms:
    """Тесты метода get_active_rooms."""

    @pytest.mark.asyncio
    async def test_get_active_rooms(self, session):
        """Тест получения активных комнат."""
        repo = RoomRepository(session)

        await repo.create_room(name="Активная 1", capacity=3, is_active=True)
        await repo.create_room(name="Активная 2", capacity=5, is_active=True)
        await repo.create_room(name="Неактивная", capacity=2, is_active=False)

        active = await repo.get_active_rooms()
        assert len(active) == 2
        for r in active:
            assert r.is_active is True

    @pytest.mark.asyncio
    async def test_get_active_rooms_empty(self, session):
        """Тест: нет активных комнат."""
        repo = RoomRepository(session)
        await repo.create_room(name="Неактивная 1", capacity=2, is_active=False)
        await repo.create_room(name="Неактивная 2", capacity=3, is_active=False)

        active = await repo.get_active_rooms()
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_get_active_rooms_all_inactive(self, session):
        """Тест: все комнаты неактивные."""
        repo = RoomRepository(session)
        await repo.create_room(name="Неактивная", capacity=2, is_active=False)

        active = await repo.get_active_rooms()
        assert active == []

    @pytest.mark.asyncio
    async def test_get_active_rooms_empty_db(self, session):
        """Тест: БД пуста."""
        repo = RoomRepository(session)
        active = await repo.get_active_rooms()
        assert len(active) == 0
