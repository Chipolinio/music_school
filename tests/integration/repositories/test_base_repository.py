"""
Тесты для BaseRepository — базовый CRUD.

Покрывает методы: create, get_by_id, get_all, update, delete.
"""

import pytest

from src.models.User import User, UserRole
from src.models.Room import Room
from src.repositories.BaseRepository import BaseRepository


class TestBaseRepositoryCreate:
    """Тесты метода create."""

    @pytest.mark.asyncio
    async def test_create_user(self, session):
        """Тест создания пользователя — ID заполнен, данные сохранены."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        result = await repo.create(user)

        assert result.id is not None
        assert result.phone == "+79991234567"
        assert result.full_name == "Тест"
        assert result.role == UserRole.STUDENT
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_create_room(self, session):
        """Тест создания комнаты."""
        repo = BaseRepository(Room, session)

        room = Room(name="Класс 1", capacity=5, is_active=True)
        result = await repo.create(room)

        assert result.id is not None
        assert result.name == "Класс 1"
        assert result.capacity == 5

    @pytest.mark.asyncio
    async def test_create_returns_instance(self, session):
        """create возвращает тот же экземпляр с заполненным ID."""
        repo = BaseRepository(User, session)
        user = User(
            phone="+79990000001",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        result = await repo.create(user)
        assert result is user
        assert result.id is not None


class TestBaseRepositoryGetById:
    """Тесты метода get_by_id."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, session):
        """Тест получения существующей записи."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        result = await repo.get_by_id(user.id)
        assert result is not None
        assert result.id == user.id
        assert result.phone == "+79991234567"
        assert result.full_name == "Тест"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, session):
        """Тест получения несуществующего ID."""
        repo = BaseRepository(User, session)
        result = await repo.get_by_id(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_zero(self, session):
        """Тест получения по ID=0."""
        repo = BaseRepository(User, session)
        result = await repo.get_by_id(0)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_after_delete(self, session):
        """Тест: после удаления get_by_id возвращает None."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        user_id = user.id

        await repo.delete(user)
        result = await repo.get_by_id(user_id)
        assert result is None


class TestBaseRepositoryGetAll:
    """Тесты метода get_all."""

    @pytest.mark.asyncio
    async def test_get_all_empty(self, session):
        """Тест получения пустого списка."""
        repo = BaseRepository(User, session)
        result = await repo.get_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, session):
        """Тест получения всех записей с пагинацией."""
        repo = BaseRepository(User, session)

        for i in range(5):
            session.add(User(
                phone=f"+799912345{i:02d}",
                full_name=f"Тест {i}",
                hashed_password="hash",
                role=UserRole.STUDENT,
                is_active=True,
            ))
        await session.flush()

        result = await repo.get_all(skip=0, limit=100)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_all_with_skip(self, session):
        """Тест пагинации: skip=2."""
        repo = BaseRepository(User, session)

        for i in range(5):
            session.add(User(
                phone=f"+799912345{i:02d}",
                full_name=f"Тест {i}",
                hashed_password="hash",
                role=UserRole.STUDENT,
                is_active=True,
            ))
        await session.flush()

        result = await repo.get_all(skip=2, limit=100)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_all_with_limit(self, session):
        """Тест пагинации: limit=2."""
        repo = BaseRepository(User, session)

        for i in range(5):
            session.add(User(
                phone=f"+799912345{i:02d}",
                full_name=f"Тест {i}",
                hashed_password="hash",
                role=UserRole.STUDENT,
                is_active=True,
            ))
        await session.flush()

        result = await repo.get_all(skip=0, limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_skip_and_limit(self, session):
        """Тест пагинации: skip=1, limit=2."""
        repo = BaseRepository(User, session)

        for i in range(5):
            session.add(User(
                phone=f"+799912345{i:02d}",
                full_name=f"Тест {i}",
                hashed_password="hash",
                role=UserRole.STUDENT,
                is_active=True,
            ))
        await session.flush()

        result = await repo.get_all(skip=1, limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_default_pagination(self, session):
        """Тест: по умолчанию skip=0, limit=100."""
        repo = BaseRepository(User, session)

        for i in range(5):
            session.add(User(
                phone=f"+799912345{i:02d}",
                full_name=f"Тест {i}",
                hashed_password="hash",
                role=UserRole.STUDENT,
                is_active=True,
            ))
        await session.flush()

        result = await repo.get_all()  # Без параметров
        assert len(result) == 5


class TestBaseRepositoryUpdate:
    """Тесты метода update."""

    @pytest.mark.asyncio
    async def test_update(self, session):
        """Тест обновления: данные обновлены."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Старое имя",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        user.full_name = "Новое имя"
        result = await repo.update(user)

        assert result.full_name == "Новое имя"
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_update_returns_instance(self, session):
        """update возвращает тот же экземпляр."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        user.full_name = "Обновлённый"
        result = await repo.update(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, session):
        """Тест обновления нескольких полей."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        user.full_name = "Обновлённый"
        user.is_active = False
        await repo.update(user)

        result = await repo.get_by_id(user.id)
        assert result.full_name == "Обновлённый"
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_update_room(self, session):
        """Тест обновления комнаты."""
        repo = BaseRepository(Room, session)

        room = Room(name="Старое название", capacity=3, is_active=True)
        session.add(room)
        await session.flush()

        room.name = "Новое название"
        room.capacity = 10
        await repo.update(room)

        result = await repo.get_by_id(room.id)
        assert result.name == "Новое название"
        assert result.capacity == 10


class TestBaseRepositoryDelete:
    """Тесты метода delete."""

    @pytest.mark.asyncio
    async def test_delete(self, session):
        """Тест удаления: запись удалена."""
        repo = BaseRepository(User, session)

        user = User(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        await repo.delete(user)

        result = await repo.get_by_id(user.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_multiple_users(self, session):
        """Тест удаления нескольких записей."""
        repo = BaseRepository(User, session)

        users = []
        for i in range(3):
            user = User(
                phone=f"+7999000000{i}",
                full_name=f"Тест {i}",
                hashed_password="hash",
                role=UserRole.STUDENT,
                is_active=True,
            )
            session.add(user)
            users.append(user)
        await session.flush()

        for user in users:
            await repo.delete(user)

        result = await repo.get_all()
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_delete_room(self, session):
        """Тест удаления комнаты."""
        repo = BaseRepository(Room, session)

        room = Room(name="Комната", capacity=3, is_active=True)
        session.add(room)
        await session.flush()
        room_id = room.id

        await repo.delete(room)

        result = await repo.get_by_id(room_id)
        assert result is None
