"""
Unit-тесты сервиса аутентификации.

Тестируются: register, login, logout, verify_token_service, get_current_user
"""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.services.auth import register, login, logout, verify_token_service, get_current_user
from src.schemas.User import UserCreate, UserResponse, UserRole
from src.services.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    AuthenticationError,
    TokenExpiredError,
)
from src.models.User import UserRole as DBUserRole


class TestRegister:
    """Тесты функции register."""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_user_repo, user_create_data, mock_user_model):
        """Тест успешной регистрации."""
        # Arrange
        mock_user_repo.get_by_phone.return_value = None

        created_user = MagicMock()
        created_user.id = 1
        created_user.phone = "+79991234567"
        created_user.full_name = "Иванов Иван"
        created_user.role = DBUserRole.STUDENT
        created_user.is_active = True
        mock_user_repo.create_user.return_value = created_user

        # Act
        response, token = await register(
            user_repository=mock_user_repo,
            user_data=user_create_data,
        )

        # Assert
        assert isinstance(response, UserResponse)
        assert response.phone == "+79991234567"
        assert response.full_name == "Иванов Иван"
        assert response.role == UserRole.STUDENT
        assert response.is_active is True
        assert isinstance(token, str)
        assert len(token) > 0

        mock_user_repo.get_by_phone.assert_called_once_with("+79991234567")
        mock_user_repo.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_existing_user(self, mock_user_repo, user_create_data, mock_user_model):
        """Тест регистрации существующего пользователя."""
        # Arrange
        mock_user_repo.get_by_phone.return_value = mock_user_model

        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await register(
                user_repository=mock_user_repo,
                user_data=user_create_data,
            )

        assert exc_info.value.phone == "+79991234567"
        mock_user_repo.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_teacher(self, mock_user_repo, user_create_teacher_data):
        """Тест регистрации преподавателя."""
        # Arrange
        mock_user_repo.get_by_phone.return_value = None

        created_user = MagicMock()
        created_user.id = 2
        created_user.phone = "+79991234568"
        created_user.full_name = "Петров Пётр"
        created_user.role = DBUserRole.TEACHER
        created_user.is_active = True
        mock_user_repo.create_user.return_value = created_user

        # Act
        response, token = await register(
            user_repository=mock_user_repo,
            user_data=user_create_teacher_data,
        )

        # Assert
        assert response.role == UserRole.TEACHER


class TestLogin:
    """Тесты функции login."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_user_repo, mock_user_model):
        """Тест успешного входа."""
        # Arrange
        from src.utils.security import get_password_hash

        mock_user_model.hashed_password = get_password_hash("SecurePass123")
        mock_user_repo.get_by_phone.return_value = mock_user_model

        # Act
        response, token = await login(
            user_repository=mock_user_repo,
            phone="+79991234567",
            password="SecurePass123",
        )

        # Assert
        assert isinstance(response, UserResponse)
        assert response.id == 1
        assert response.phone == "+79991234567"
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_user_repo):
        """Тест входа несуществующего пользователя."""
        # Arrange
        mock_user_repo.get_by_phone.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await login(
                user_repository=mock_user_repo,
                phone="+79999999999",
                password="AnyPassword",
            )

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_user_repo, mock_user_model):
        """Тест входа с неверным паролем."""
        # Arrange
        from src.utils.security import get_password_hash

        mock_user_model.hashed_password = get_password_hash("CorrectPassword")
        mock_user_repo.get_by_phone.return_value = mock_user_model

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await login(
                user_repository=mock_user_repo,
                phone="+79991234567",
                password="WrongPassword",
            )

        assert "Неверный пароль" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_user_repo, mock_user_model):
        """Тест входа неактивного пользователя."""
        # Arrange
        from src.utils.security import get_password_hash

        mock_user_model.is_active = False
        mock_user_model.hashed_password = get_password_hash("SecurePass123")
        mock_user_repo.get_by_phone.return_value = mock_user_model

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await login(
                user_repository=mock_user_repo,
                phone="+79991234567",
                password="SecurePass123",
            )

        assert "неактивен" in str(exc_info.value).lower()


class TestLogout:
    """Тесты функции logout."""

    def test_logout(self, caplog):
        """Тест выхода — просто логирует."""
        # Act
        with caplog.at_level(logging.INFO):
            logout("some_token")

        # Assert — проверяем, что лог записался (stateless logout)
        assert "Выход пользователя" in caplog.text


class TestVerifyTokenService:
    """Тесты функции verify_token_service."""

    def test_verify_valid_token(self, valid_token):
        """Тест проверки валидного токена."""
        # Arrange
        payload = {"sub": "1", "role": "STUDENT", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
        with patch("src.services.auth.decode_token", return_value=payload):
            # Act
            result = verify_token_service(valid_token)

            # Assert
            assert result["sub"] == "1"
            assert result["role"] == "STUDENT"

    def test_verify_expired_token(self, expired_token):
        """Тест проверки протухшего токена."""
        # Arrange
        from jose import ExpiredSignatureError
        with patch("src.services.auth.decode_token", side_effect=ExpiredSignatureError):
            # Act & Assert
            with pytest.raises(TokenExpiredError):
                verify_token_service(expired_token)

    def test_verify_invalid_token(self):
        """Тест проверки невалидного токена."""
        # Arrange
        from jose import JWTError
        with patch("src.services.auth.decode_token", side_effect=JWTError("bad token")):
            # Act & Assert
            with pytest.raises(AuthenticationError):
                verify_token_service("invalid_token")


class TestGetCurrentUser:
    """Тесты функции get_current_user."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user_repo, mock_user_model):
        """Тест успешного получения текущего пользователя."""
        # Arrange
        payload = {"sub": "1", "role": "STUDENT"}
        mock_user_repo.get_by_id.return_value = mock_user_model

        with patch("src.services.auth.decode_token", return_value=payload):
            # Act
            response = await get_current_user(
                user_repository=mock_user_repo,
                token="valid_token",
            )

            # Assert
            assert response.id == 1
            assert response.phone == "+79991234567"
            assert response.role == UserRole.STUDENT

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_user_repo):
        """Тест когда пользователь из токена не найден."""
        # Arrange
        payload = {"sub": "999", "role": "STUDENT"}
        mock_user_repo.get_by_id.return_value = None

        with patch("src.services.auth.decode_token", return_value=payload):
            # Act & Assert
            with pytest.raises(UserNotFoundError):
                await get_current_user(
                    user_repository=mock_user_repo,
                    token="valid_token",
                )
