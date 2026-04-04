"""
Unit-тесты для error handler (error_handler.py).
Маппинг исключений → HTTP-статусы.
"""

import json
import pytest
from unittest.mock import MagicMock
from fastapi import status
from fastapi.responses import JSONResponse

from src.api.error_handler import service_exception_handler
from src.services.exceptions import (
    ServiceError, UserNotFoundError, AuthenticationError,
    InvalidRoleError, UserAlreadyExistsError, SlotConflictError,
    CapacityExceededError,
)


class TestServiceExceptionHandler:
    async def test_user_not_found(self):
        request = MagicMock()
        exc = UserNotFoundError(user_id=999)
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        body = json.loads(response.body)
        assert body["error"] == "UserNotFoundError"

    async def test_authentication_error(self):
        request = MagicMock()
        exc = AuthenticationError("Неверный пароль")
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert json.loads(response.body)["error"] == "AuthenticationError"

    async def test_invalid_role_error(self):
        request = MagicMock()
        exc = InvalidRoleError("Требуется ADMIN")
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert json.loads(response.body)["error"] == "InvalidRoleError"

    async def test_user_already_exists_error(self):
        request = MagicMock()
        exc = UserAlreadyExistsError(phone="+79991234567")
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.body)["error"] == "UserAlreadyExistsError"

    async def test_slot_conflict_error(self):
        request = MagicMock()
        exc = SlotConflictError("Преподаватель занят")
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert json.loads(response.body)["error"] == "SlotConflictError"

    async def test_capacity_exceeded_error(self):
        request = MagicMock()
        exc = CapacityExceededError(slot_id=1, max_participants=3)
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.body)["error"] == "CapacityExceededError"

    async def test_unknown_service_error(self):
        request = MagicMock()
        exc = ServiceError("Неизвестная ошибка")
        response = await service_exception_handler(request, exc)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
