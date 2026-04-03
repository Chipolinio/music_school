"""
Integration-тесты сервиса аутентификации.

Тестируются с реальной БД: register, login, get_current_user
"""

import pytest
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth import register, login, get_current_user
from src.schemas.User import UserCreate, UserResponse, UserRole
from src.services.exceptions import UserAlreadyExistsError, UserNotFoundError, AuthenticationError
from src.utils.security import get_password_hash, verify_password
from src.models.User import User as UserModel
from src.repositories.UserRepository import UserRepository


class TestAuthIntegration:
    """Integration-тесты аутентификации."""

    @pytest.mark.asyncio
    async def test_register_and_login(self, session: AsyncSession, user_repo: UserRepository):
        """Тест: регистрация + вход с реальным хэшированием."""
        # Register
        user_data = UserCreate(
            phone="+79001001001",
            full_name="Тестовый Пользователь",
            password="Password123!",
            role=UserRole.STUDENT,
        )

        response, token = await register(user_repo, user_data)

        assert response.phone == "+79001001001"
        assert response.full_name == "Тестовый Пользователь"
        assert response.role == UserRole.STUDENT
        assert response.is_active is True
        assert isinstance(token, str) and len(token) > 0

        # Verify password was hashed
        db_user = await session.get(UserModel, response.id)
        assert db_user is not None
        assert verify_password("Password123!", db_user.hashed_password)

        # Login
        login_response, login_token = await login(user_repo, "+79001001001", "Password123!")
        assert login_response.id == response.id
        assert isinstance(login_token, str)

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, session: AsyncSession, user_repo: UserRepository):
        """Тест: регистрация с дублирующимся телефоном."""
        user_data = UserCreate(
            phone="+79001001002",
            full_name="Первый",
            password="Password123!",
        )
        await register(user_repo, user_data)

        user_data2 = UserCreate(
            phone="+79001001002",
            full_name="Второй",
            password="Password123!",
        )

        with pytest.raises(UserAlreadyExistsError):
            await register(user_repo, user_data2)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, session: AsyncSession, user_repo: UserRepository):
        """Тест: вход с неверным паролем."""
        user_data = UserCreate(
            phone="+79001001003",
            full_name="Тест",
            password="CorrectPassword",
        )
        await register(user_repo, user_data)

        with pytest.raises(AuthenticationError):
            await login(user_repo, "+79001001003", "WrongPassword")

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, session: AsyncSession, user_repo: UserRepository):
        """Тест: вход неактивного пользователя."""
        user_data = UserCreate(
            phone="+79001001004",
            full_name="Неактивный",
            password="Password123!",
        )
        response, _ = await register(user_repo, user_data)

        # Деактивируем
        db_user = await session.get(UserModel, response.id)
        db_user.is_active = False
        await session.commit()

        with pytest.raises(AuthenticationError):
            await login(user_repo, "+79001001004", "Password123!")

    @pytest.mark.asyncio
    async def test_get_current_user(self, session: AsyncSession, user_repo: UserRepository):
        """Тест: получение текущего пользователя после регистрации."""
        user_data = UserCreate(
            phone="+79001001005",
            full_name="Текущий",
            password="Password123!",
        )
        _, token = await register(user_repo, user_data)

        result = await get_current_user(user_repo, token)

        assert result.phone == "+79001001005"
        assert result.full_name == "Текущий"
