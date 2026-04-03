"""
Unit-тесты сервиса управления пользователями.

Тестируются: get_user_by_id, get_all_users, update_user, deactivate_user, activate_user
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.user import get_user_by_id, get_all_users, update_user, deactivate_user, activate_user
from src.schemas.User import UserResponse, UserUpdate, UserRole
from src.services.exceptions import UserNotFoundError, InvalidRoleError, UserAlreadyExistsError
from src.models.User import UserRole as DBUserRole


class TestGetUserById:
    """Тесты функции get_user_by_id."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_user_repo, mock_user_model):
        """Тест успешного получения пользователя."""
        # Arrange
        mock_user_repo.get_by_id.return_value = mock_user_model

        # Act
        response = await get_user_by_id(mock_user_repo, 1)

        # Assert
        assert isinstance(response, UserResponse)
        assert response.id == 1
        assert response.phone == "+79991234567"
        assert response.role == UserRole.STUDENT

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_user_repo):
        """Тест когда пользователь не найден."""
        # Arrange
        mock_user_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError) as exc_info:
            await get_user_by_id(mock_user_repo, 999)

        assert "999" in str(exc_info.value)


class TestGetAllUsers:
    """Тесты функции get_all_users."""

    @pytest.mark.asyncio
    async def test_get_all_users_no_filter(self, mock_user_repo, mock_user_model):
        """Тест получения списка без фильтра."""
        # Arrange
        mock_user_repo.get_all.return_value = [mock_user_model]

        # Act
        result = await get_all_users(mock_user_repo, skip=0, limit=10)

        # Assert
        assert len(result) == 1
        assert result[0].id == 1
        mock_user_repo.get_all.assert_called_once_with(skip=0, limit=10, role=None)

    @pytest.mark.asyncio
    async def test_get_all_users_with_role_filter(self, mock_user_repo, mock_user_model):
        """Тест получения списка с фильтром по роли."""
        # Arrange
        mock_user_repo.get_all.return_value = [mock_user_model]

        # Act
        result = await get_all_users(mock_user_repo, skip=0, limit=10, role=UserRole.STUDENT)

        # Assert
        assert len(result) == 1
        mock_user_repo.get_all.assert_called_once_with(skip=0, limit=10, role=UserRole.STUDENT)

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, mock_user_repo):
        """Тест получения пустого списка."""
        # Arrange
        mock_user_repo.get_all.return_value = []

        # Act
        result = await get_all_users(mock_user_repo, skip=0, limit=10)

        # Assert
        assert result == []


class TestUpdateUser:
    """Тесты функции update_user."""

    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_user_repo, mock_user_model):
        """Тест успешного обновления."""
        # Arrange
        update_data = UserUpdate(full_name="Новое Имя")
        mock_user_repo.get_by_id.return_value = mock_user_model

        updated_user = MagicMock()
        updated_user.id = 1
        updated_user.phone = "+79991234567"
        updated_user.full_name = "Новое Имя"
        updated_user.role = DBUserRole.STUDENT
        updated_user.is_active = True
        mock_user_repo.update.return_value = updated_user

        # Act
        response = await update_user(mock_user_repo, 1, update_data, UserRole.ADMIN)

        # Assert
        assert response.full_name == "Новое Имя"
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_user_repo):
        """Тест обновления несуществующего пользователя."""
        # Arrange
        mock_user_repo.get_by_id.return_value = None
        update_data = UserUpdate(full_name="Новое Имя")

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await update_user(mock_user_repo, 999, update_data, UserRole.ADMIN)

    @pytest.mark.asyncio
    async def test_update_user_role_non_admin_forbidden(self, mock_user_repo, mock_user_model):
        """Тест смены роли без прав ADMIN."""
        # Arrange
        update_data = UserUpdate(role=UserRole.ADMIN)
        mock_user_repo.get_by_id.return_value = mock_user_model

        # Act & Assert
        with pytest.raises(InvalidRoleError) as exc_info:
            await update_user(mock_user_repo, 1, update_data, UserRole.STUDENT)

        assert "Только ADMIN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_user_phone_taken(self, mock_user_repo, mock_user_model):
        """Тест обновления на занятый телефон."""
        # Arrange
        update_data = UserUpdate(phone="+79990000000")
        mock_user_repo.get_by_id.return_value = mock_user_model

        other_user = MagicMock()
        other_user.id = 99
        mock_user_repo.get_by_phone.return_value = other_user

        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await update_user(mock_user_repo, 1, update_data, UserRole.ADMIN)

        assert exc_info.value.phone == "+79990000000"

    @pytest.mark.asyncio
    async def test_update_user_same_phone_allowed(self, mock_user_repo, mock_user_model):
        """Тест обновления на свой же телефон — разрешено."""
        # Arrange
        update_data = UserUpdate(phone="+79991234567")
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_user_repo.get_by_phone.return_value = mock_user_model  # Тот же юзер

        updated_user = MagicMock()
        updated_user.id = 1
        updated_user.phone = "+79991234567"
        updated_user.full_name = "Иванов Иван"
        updated_user.role = DBUserRole.STUDENT
        updated_user.is_active = True
        mock_user_repo.update.return_value = updated_user

        # Act
        response = await update_user(mock_user_repo, 1, update_data, UserRole.ADMIN)

        # Assert
        assert response.phone == "+79991234567"


class TestDeactivateUser:
    """Тесты функции deactivate_user."""

    @pytest.mark.asyncio
    async def test_deactivate_success(self, mock_user_repo, mock_user_model):
        """Тест успешной деактивации админом."""
        # Arrange
        mock_user_repo.get_by_id.return_value = mock_user_model

        updated_user = MagicMock()
        updated_user.id = 1
        updated_user.phone = "+79991234567"
        updated_user.full_name = "Иванов Иван"
        updated_user.role = DBUserRole.STUDENT
        updated_user.is_active = False
        mock_user_repo.update.return_value = updated_user

        # Act
        response = await deactivate_user(mock_user_repo, 1, UserRole.ADMIN)

        # Assert
        assert response.is_active is False
        assert mock_user_model.is_active is False  # Проверяем, что флаг изменён

    @pytest.mark.asyncio
    async def test_deactivate_non_admin_forbidden(self, mock_user_repo):
        """Тест деактивации без прав ADMIN."""
        # Act & Assert
        with pytest.raises(InvalidRoleError) as exc_info:
            await deactivate_user(mock_user_repo, 1, UserRole.STUDENT)

        assert "Только ADMIN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, mock_user_repo):
        """Тест деактивации несуществующего пользователя."""
        # Arrange
        mock_user_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await deactivate_user(mock_user_repo, 999, UserRole.ADMIN)


class TestActivateUser:
    """Тесты функции activate_user."""

    @pytest.mark.asyncio
    async def test_activate_success(self, mock_user_repo):
        """Тест успешной активации админом."""
        # Arrange
        inactive_user = MagicMock()
        inactive_user.id = 1
        inactive_user.phone = "+79991234567"
        inactive_user.full_name = "Иванов Иван"
        inactive_user.role = DBUserRole.STUDENT
        inactive_user.is_active = False
        mock_user_repo.get_by_id.return_value = inactive_user

        updated_user = MagicMock()
        updated_user.id = 1
        updated_user.phone = "+79991234567"
        updated_user.full_name = "Иванов Иван"
        updated_user.role = DBUserRole.STUDENT
        updated_user.is_active = True
        mock_user_repo.update.return_value = updated_user

        # Act
        response = await activate_user(mock_user_repo, 1, UserRole.ADMIN)

        # Assert
        assert response.is_active is True
        assert inactive_user.is_active is True

    @pytest.mark.asyncio
    async def test_activate_non_admin_forbidden(self, mock_user_repo):
        """Тест активации без прав ADMIN."""
        # Act & Assert
        with pytest.raises(InvalidRoleError):
            await activate_user(mock_user_repo, 1, UserRole.STUDENT)

    @pytest.mark.asyncio
    async def test_activate_user_not_found(self, mock_user_repo):
        """Тест активации несуществующего пользователя."""
        # Arrange
        mock_user_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await activate_user(mock_user_repo, 999, UserRole.ADMIN)
