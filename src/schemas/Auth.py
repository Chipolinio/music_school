"""
Схемы для аутентификации API.
"""

from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict

from src.schemas.User import UserResponse


class LoginRequest(BaseModel):
    """Запрос на вход пользователя."""
    phone: Annotated[str, Field(
        ...,
        min_length=10,
        max_length=20,
        description="Номер телефона",
        examples=["+79991234567"]
    )]
    password: Annotated[str, Field(
        ...,
        min_length=8,
        max_length=100,
        description="Пароль пользователя"
    )]

    model_config = ConfigDict(str_strip_whitespace=True)


class AuthResponse(BaseModel):
    """Ответ аутентификации: пользователь и сообщение."""
    user: UserResponse
    message: Annotated[str, Field(
        ...,
        description="Сообщение об успехе",
        examples=["Успешный вход"]
    )]

    model_config = ConfigDict(from_attributes=True)


class LogoutResponse(BaseModel):
    """Ответ на выход пользователя."""
    message: Annotated[str, Field(
        ...,
        description="Сообщение об успехе",
        examples=["Успешный выход"]
    )]


class TokenVerifyResponse(BaseModel):
    """Ответ проверки JWT-токена."""
    valid: Annotated[bool, Field(
        ...,
        description="Валиден ли токен"
    )]
    payload: Annotated[dict, Field(
        ...,
        description="Данные токена (user_id, role, exp)"
    )]
