"""
Тесты для UserRepository.

Покрывает методы: get_by_phone, get_by_id, get_all, create_user.

Чеклист (раздел 5.2):
| Метод | Тест |
|-------|------|
| `get_by_phone` | Найден / Не найден |
| `get_by_id` | Переопределение базового |
| `get_all` | Без фильтра / С фильтром по роли / Пустой |
| `create_user` | Создание с преобразованием роли (STUDENT, TEACHER, ADMIN) |
"""

import pytest

from src.models.User import User, UserRole
from src.repositories.UserRepository import UserRepository


class TestUserRepositoryGetByPhone:
    """Тесты метода get_by_phone."""

    @pytest.mark.asyncio
    async def test_get_by_phone_found(self, session):
        """Тест поиска по телефону: найден."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79991234567",
            full_name="Иванов Иван",
            hashed_password="hash",
            role="STUDENT",
        )

        found = await repo.get_by_phone("+79991234567")
        assert found is not None
        assert found.id == user.id
        assert found.phone == "+79991234567"
        assert found.full_name == "Иванов Иван"

    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(self, session):
        """Тест поиска несуществующего телефона."""
        repo = UserRepository(session)
        found = await repo.get_by_phone("+79990000000")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_phone_returns_correct_role(self, session):
        """Тест: get_by_phone возвращает пользователя с правильной ролью."""
        repo = UserRepository(session)

        await repo.create_user(
            phone="+79991234567",
            full_name="Преподаватель",
            hashed_password="hash",
            role="TEACHER",
        )

        found = await repo.get_by_phone("+79991234567")
        assert found is not None
        assert found.role == UserRole.TEACHER


class TestUserRepositoryGetById:
    """Тесты метода get_by_id (переопределение базового)."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, session):
        """Тест получения по ID: найден."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79991234567",
            full_name="Иванов Иван",
            hashed_password="hash",
            role="STUDENT",
        )

        found = await repo.get_by_id(user.id)
        assert found is not None
        assert found.id == user.id
        assert found.phone == "+79991234567"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, session):
        """Тест получения несуществующего ID."""
        repo = UserRepository(session)
        found = await repo.get_by_id(99999)
        assert found is None


class TestUserRepositoryGetAll:
    """Тесты метода get_all."""

    @pytest.mark.asyncio
    async def test_get_all_no_filter(self, session):
        """Тест получения всех без фильтра."""
        repo = UserRepository(session)

        await repo.create_user(phone="+79991111111", full_name="Студент", hashed_password="h", role="STUDENT")
        await repo.create_user(phone="+79992222222", full_name="Преподаватель", hashed_password="h", role="TEACHER")

        all_users = await repo.get_all()
        assert len(all_users) == 2

    @pytest.mark.asyncio
    async def test_get_all_empty(self, session):
        """Тест получения пустого списка."""
        repo = UserRepository(session)
        all_users = await repo.get_all()
        assert len(all_users) == 0

    @pytest.mark.asyncio
    async def test_get_all_with_role_filter_student(self, session):
        """Тест получения всех с фильтром по роли: STUDENT."""
        repo = UserRepository(session)

        await repo.create_user(phone="+79991111111", full_name="Студент 1", hashed_password="h", role="STUDENT")
        await repo.create_user(phone="+79992222222", full_name="Студент 2", hashed_password="h", role="STUDENT")
        await repo.create_user(phone="+79993333333", full_name="Преподаватель", hashed_password="h", role="TEACHER")

        students = await repo.get_all(role=UserRole.STUDENT)
        assert len(students) == 2
        for s in students:
            assert s.role == UserRole.STUDENT

    @pytest.mark.asyncio
    async def test_get_all_with_role_filter_teacher(self, session):
        """Тест получения всех с фильтром по роли: TEACHER."""
        repo = UserRepository(session)

        await repo.create_user(phone="+79991111111", full_name="Студент", hashed_password="h", role="STUDENT")
        await repo.create_user(phone="+79992222222", full_name="Преподаватель", hashed_password="h", role="TEACHER")
        await repo.create_user(phone="+79993333333", full_name="Админ", hashed_password="h", role="ADMIN")

        teachers = await repo.get_all(role=UserRole.TEACHER)
        assert len(teachers) == 1
        assert teachers[0].role == UserRole.TEACHER

    @pytest.mark.asyncio
    async def test_get_all_with_role_filter_admin(self, session):
        """Тест получения всех с фильтром по роли: ADMIN."""
        repo = UserRepository(session)

        await repo.create_user(phone="+79991111111", full_name="Студент", hashed_password="h", role="STUDENT")
        await repo.create_user(phone="+79993333333", full_name="Админ", hashed_password="h", role="ADMIN")

        admins = await repo.get_all(role=UserRole.ADMIN)
        assert len(admins) == 1
        assert admins[0].role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_get_all_with_role_filter_no_match(self, session):
        """Тест: фильтр по роли, которой нет в БД."""
        repo = UserRepository(session)

        await repo.create_user(phone="+79991111111", full_name="Студент", hashed_password="h", role="STUDENT")

        teachers = await repo.get_all(role=UserRole.TEACHER)
        assert len(teachers) == 0

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, session):
        """Тест получения с пагинацией."""
        repo = UserRepository(session)

        for i in range(5):
            await repo.create_user(
                phone=f"+7999100000{i}",
                full_name=f"Пользователь {i}",
                hashed_password="h",
                role="STUDENT",
            )

        result = await repo.get_all(skip=2, limit=2)
        assert len(result) == 2


class TestUserRepositoryCreateUser:
    """Тесты метода create_user."""

    @pytest.mark.asyncio
    async def test_create_user_student_role(self, session):
        """Тест создания пользователя с ролью STUDENT."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79991111111",
            full_name="Студент",
            hashed_password="hash",
            role="STUDENT",
        )

        assert user.id is not None
        assert user.phone == "+79991111111"
        assert user.full_name == "Студент"
        assert user.role == UserRole.STUDENT
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_user_teacher_role(self, session):
        """Тест создания пользователя с ролью TEACHER."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79992222222",
            full_name="Преподаватель",
            hashed_password="hash",
            role="TEACHER",
        )

        assert user.id is not None
        assert user.role == UserRole.TEACHER

    @pytest.mark.asyncio
    async def test_create_user_admin_role(self, session):
        """Тест создания пользователя с ролью ADMIN."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79993333333",
            full_name="Админ",
            hashed_password="hash",
            role="ADMIN",
        )

        assert user.id is not None
        assert user.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_create_user_default_is_active(self, session):
        """Тест: is_active=True по умолчанию."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79991111111",
            full_name="Студент",
            hashed_password="hash",
            role="STUDENT",
        )

        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_user_is_active_false(self, session):
        """Тест создания пользователя с is_active=False."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79991111111",
            full_name="Неактивный",
            hashed_password="hash",
            role="STUDENT",
            is_active=False,
        )

        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_create_user_returns_instance(self, session):
        """create_user возвращает тот же экземпляр с заполненным ID."""
        repo = UserRepository(session)

        user = await repo.create_user(
            phone="+79991234567",
            full_name="Тест",
            hashed_password="hash",
            role="STUDENT",
        )

        assert user.id is not None
        assert isinstance(user, User)
