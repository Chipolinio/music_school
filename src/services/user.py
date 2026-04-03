"""
Сервис управления пользователями.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import List, Optional

from src.repositories.UserRepository import UserRepository
from src.schemas.User import UserCreate, UserResponse, UserUpdate
from src.schemas.User import UserRole
from src.services.exceptions import (
    UserNotFoundError,
    InvalidRoleError,
    UserAlreadyExistsError,
)

logger = logging.getLogger(__name__)


async def get_user_by_id(
    user_repository: UserRepository,
    user_id: int,
) -> UserResponse:
    """
    Получает пользователя по ID.

    Args:
        user_repository: Репозиторий пользователей
        user_id: ID пользователя

    Returns:
        UserResponse: Данные пользователя

    Raises:
        UserNotFoundError: если пользователь не найден
    """
    logger.debug(f"Получение пользователя по ID: {user_id}")

    user = await user_repository.get_by_id(user_id)
    if user is None:
        logger.warning(f"Пользователь с ID {user_id} не найден")
        raise UserNotFoundError(user_id=user_id)

    return UserResponse(
        id=user.id,
        phone=user.phone,
        full_name=user.full_name,
        role=UserRole(user.role.value),
        is_active=user.is_active,
    )


async def get_all_users(
    user_repository: UserRepository,
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
) -> List[UserResponse]:
    """
    Получает список пользователей с пагинацией и опциональной фильтрацией по роли.

    Args:
        user_repository: Репозиторий пользователей
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        role: Опциональная фильтрация по роли

    Returns:
        List[UserResponse]: Список пользователей
    """
    logger.debug(f"Получение списка пользователей: skip={skip}, limit={limit}, role={role}")

    users = await user_repository.get_all(skip=skip, limit=limit, role=role)
    return [
        UserResponse(
            id=u.id,
            phone=u.phone,
            full_name=u.full_name,
            role=UserRole(u.role.value),
            is_active=u.is_active,
        )
        for u in users
    ]


async def update_user(
    user_repository: UserRepository,
    user_id: int,
    update_data: UserUpdate,
    current_user_role: UserRole,
) -> UserResponse:
    """
    Обновляет данные пользователя.

    Args:
        user_repository: Репозиторий пользователей
        user_id: ID пользователя для обновления
        update_data: Данные для обновления
        current_user_role: Роль текущего пользователя (для проверки прав)

    Returns:
        UserResponse: Обновлённые данные пользователя

    Raises:
        UserNotFoundError: если пользователь не найден
        InvalidRoleError: если недостаточно прав для смены роли
        UserAlreadyExistsError: если новый телефон уже занят
    """
    logger.debug(f"Обновление пользователя {user_id}")

    user = await user_repository.get_by_id(user_id)
    if user is None:
        logger.warning(f"Пользователь с ID {user_id} не найден для обновления")
        raise UserNotFoundError(user_id=user_id)

    update_dict = update_data.model_dump(exclude_unset=True)

    if "role" in update_dict and update_dict["role"] is not None:
        if update_dict["role"] != user.role.value and current_user_role != UserRole.ADMIN:
            logger.warning(
                f"Пользователь с ролью {current_user_role} попытался изменить роль пользователя {user_id}"
            )
            raise InvalidRoleError("Только ADMIN может менять роль пользователя")

    if "phone" in update_dict:
        existing_user = await user_repository.get_by_phone(update_dict["phone"])
        if existing_user and existing_user.id != user_id:
            logger.warning(f"Телефон {update_dict['phone']} уже занят")
            raise UserAlreadyExistsError(update_dict["phone"])

    for field, value in update_dict.items():
        if value is not None:
            setattr(user, field, value)

    updated_user = await user_repository.update(user)
    await user_repository.session.commit()
    logger.info(f"Пользователь {user_id} успешно обновлён")

    return UserResponse(
        id=updated_user.id,
        phone=updated_user.phone,
        full_name=updated_user.full_name,
        role=UserRole(updated_user.role.value),
        is_active=updated_user.is_active,
    )


async def deactivate_user(
    user_repository: UserRepository,
    user_id: int,
    current_user_role: UserRole,
) -> UserResponse:
    """
    Деактивирует пользователя (блокировка).

    Args:
        user_repository: Репозиторий пользователей
        user_id: ID пользователя для деактивации
        current_user_role: Роль текущего пользователя (для проверки прав)

    Returns:
        UserResponse: Обновлённые данные пользователя

    Raises:
        UserNotFoundError: если пользователь не найден
        InvalidRoleError: если недостаточно прав
    """
    logger.debug(f"Деактивация пользователя {user_id}")

    if current_user_role != UserRole.ADMIN:
        logger.warning(
            f"Пользователь с ролью {current_user_role} попытался деактивировать пользователя {user_id}"
        )
        raise InvalidRoleError("Только ADMIN может деактивировать пользователей")

    user = await user_repository.get_by_id(user_id)
    if user is None:
        logger.warning(f"Пользователь с ID {user_id} не найден для деактивации")
        raise UserNotFoundError(user_id=user_id)

    user.is_active = False
    updated_user = await user_repository.update(user)
    await user_repository.session.commit()
    logger.info(f"Пользователь {user_id} успешно деактивирован")

    return UserResponse(
        id=updated_user.id,
        phone=updated_user.phone,
        full_name=updated_user.full_name,
        role=UserRole(updated_user.role.value),
        is_active=updated_user.is_active,
    )


async def activate_user(
    user_repository: UserRepository,
    user_id: int,
    current_user_role: UserRole,
) -> UserResponse:
    """
    Активирует пользователя (разблокировка).

    Args:
        user_repository: Репозиторий пользователей
        user_id: ID пользователя для активации
        current_user_role: Роль текущего пользователя (для проверки прав)

    Returns:
        UserResponse: Обновлённые данные пользователя

    Raises:
        UserNotFoundError: если пользователь не найден
        InvalidRoleError: если недостаточно прав
    """
    logger.debug(f"Активация пользователя {user_id}")

    if current_user_role != UserRole.ADMIN:
        logger.warning(
            f"Пользователь с ролью {current_user_role} попытался активировать пользователя {user_id}"
        )
        raise InvalidRoleError("Только ADMIN может активировать пользователей")

    user = await user_repository.get_by_id(user_id)
    if user is None:
        logger.warning(f"Пользователь с ID {user_id} не найден для активации")
        raise UserNotFoundError(user_id=user_id)

    user.is_active = True
    updated_user = await user_repository.update(user)
    await user_repository.session.commit()
    logger.info(f"Пользователь {user_id} успешно активирован")

    return UserResponse(
        id=updated_user.id,
        phone=updated_user.phone,
        full_name=updated_user.full_name,
        role=UserRole(updated_user.role.value),
        is_active=updated_user.is_active,
    )
