"""
Сервис аутентификации и регистрации пользователей.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import Tuple

from src.repositories.UserRepository import UserRepository
from src.schemas.User import UserCreate, UserResponse
from src.schemas.User import UserRole as UserRoleSchema
from src.utils.security import get_password_hash, verify_password, create_token, decode_token
from src.services.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)


async def register(
    user_repository: UserRepository,
    user_data: UserCreate,
) -> Tuple[UserResponse, str]:
    """
    Регистрирует нового пользователя.
    """
    logger.debug(f"Попытка регистрации пользователя с телефоном {user_data.phone}")

    existing_user = await user_repository.get_by_phone(user_data.phone)
    if existing_user is not None:
        logger.warning(f"Попытка регистрации существующего пользователя: {user_data.phone}")
        raise UserAlreadyExistsError(user_data.phone)

    hashed_pw = get_password_hash(user_data.password)

    created_user = await user_repository.create_user(
        phone=user_data.phone,
        full_name=user_data.full_name,
        hashed_password=hashed_pw,
        role=user_data.role.value if user_data.role else "STUDENT",
    )
    await user_repository.session.commit()
    logger.info(f"Успешная регистрация пользователя: {created_user.phone}")

    token = create_token(
        data_dict={"sub": str(created_user.id), "role": created_user.role.value},
        duration=1800,
    )

    response = UserResponse(
        id=created_user.id,
        phone=created_user.phone,
        full_name=created_user.full_name,
        role=UserRoleSchema(created_user.role.value),
        is_active=created_user.is_active,
    )

    return response, token


async def login(
    user_repository: UserRepository,
    phone: str,
    password: str,
) -> Tuple[UserResponse, str]:
    """
    Авторизует пользователя.

    Args:
        user_repository: Репозиторий пользователей
        phone: Номер телефона пользователя
        password: Пароль пользователя

    Returns:
        Tuple[UserResponse, str]: Данные пользователя и JWT-токен

    Raises:
        UserNotFoundError: если пользователь не найден
        AuthenticationError: если пароль неверный или аккаунт неактивен
    """
    logger.debug(f"Попытка входа пользователя с телефоном {phone}")

    user = await user_repository.get_by_phone(phone)
    if user is None:
        logger.warning(f"Попытка входа несуществующего пользователя: {phone}")
        raise UserNotFoundError(phone=phone)

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Неверный пароль для пользователя: {phone}")
        raise AuthenticationError("Неверный пароль")

    if not user.is_active:
        logger.warning(f"Попытка входа неактивного пользователя: {phone}")
        raise AuthenticationError("Аккаунт неактивен")

    token = create_token(
        data_dict={"sub": str(user.id), "role": user.role.value},
        duration=1800,
    )
    logger.info(f"Успешный вход пользователя: {phone}")

    response = UserResponse(
        id=user.id,
        phone=user.phone,
        full_name=user.full_name,
        role=UserRoleSchema(user.role.value),
        is_active=user.is_active,
    )

    return response, token


def logout(token: str) -> None:
    """
    Выход пользователя.

    В stateless-архитектуре это просто логирование — очистка токена
    происходит на клиенте.
    """
    logger.info(f"Выход пользователя (токен аннулирован на клиенте)")


def verify_token_service(token: str) -> dict:
    """
    Проверяет валидность JWT-токена.

    Args:
        token: JWT-токен для проверки

    Returns:
        dict: payload токена (user_id, role, exp)

    Raises:
        TokenExpiredError: если токен истёк
        AuthenticationError: если токен невалиден
    """
    from jose import ExpiredSignatureError, JWTError
    try:
        return decode_token(token)
    except ExpiredSignatureError:
        logger.warning("Попытка использования истёкшего токена")
        raise TokenExpiredError("JWT-токен истёк")
    except JWTError as e:
        logger.warning(f"Ошибка проверки токена: {e}")
        raise AuthenticationError("Невалидный JWT-токен")


async def get_current_user(
    user_repository: UserRepository,
    token: str,
) -> UserResponse:
    """
    Получает данные текущего пользователя.

    Args:
        user_repository: Репозиторий пользователей
        token: JWT-токен пользователя

    Returns:
        UserResponse: Данные пользователя

    Raises:
        AuthenticationError: если токен невалиден
        UserNotFoundError: если пользователь не найден
    """
    payload = verify_token_service(token)
    user_id = int(payload.get("sub"))

    user = await user_repository.get_by_id(user_id)
    if user is None:
        logger.warning(f"Пользователь {user_id} не найден при проверке токена")
        raise UserNotFoundError(user_id=user_id)

    return UserResponse(
        id=user.id,
        phone=user.phone,
        full_name=user.full_name,
        role=UserRoleSchema(user.role.value),
        is_active=user.is_active,
    )
