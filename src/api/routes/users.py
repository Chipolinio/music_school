"""
API роуты для пользователей.
"""

from fastapi import APIRouter, Depends, status
from typing import Optional

from src.api.deps import get_user_service, UserService, get_current_user_from_request, require_admin
from src.schemas.User import UserResponse, UserRole, UserListResponse, UserUpdateRequest, UserUpdateResponse, UserDeactivateResponse, UserActivateResponse


router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Получение пользователя по ID."""
    return await service.get_by_id(user_id)


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    service: UserService = Depends(get_user_service),
):
    """Получение списка пользователей с пагинацией и фильтрацией по роли."""
    users = await service.get_all(skip=skip, limit=limit, role=role)
    return UserListResponse(users=users, total=len(users))


@router.patch("/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    user_data: dict = Depends(get_current_user_from_request),
    service: UserService = Depends(get_user_service),
):
    """Обновление данных пользователя."""
    current_role = UserRole(user_data["role"])
    user = await service.update(user_id, update_data, current_role)
    return UserUpdateResponse(user=user, message="Пользователь успешно обновлён")


@router.post("/{user_id}/deactivate", response_model=UserDeactivateResponse)
async def deactivate_user(
    user_id: int,
    user_data: dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Деактивация пользователя (только ADMIN)."""
    current_role = UserRole(user_data["role"])
    user = await service.deactivate(user_id, current_role)
    return UserDeactivateResponse(user=user, message="Пользователь успешно деактивирован")


@router.post("/{user_id}/activate", response_model=UserActivateResponse)
async def activate_user(
    user_id: int,
    user_data: dict = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Активация пользователя (только ADMIN)."""
    current_role = UserRole(user_data["role"])
    user = await service.activate(user_id, current_role)
    return UserActivateResponse(user=user, message="Пользователь успешно активирован")
