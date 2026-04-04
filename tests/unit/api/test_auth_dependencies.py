"""
Unit-тесты для auth-зависимостей (deps.py).
get_current_user_from_request, require_admin
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status

from src.api.deps import get_current_user_from_request, require_admin


class TestGetCurrentUserFromRequest:
    @pytest.mark.asyncio
    async def test_success_with_valid_token(self):
        mock_user = MagicMock()
        mock_auth_service = MagicMock()
        mock_auth_service.verify_token.return_value = {
            "sub": "1", "role": "STUDENT", "exp": 9999999999,
        }
        mock_auth_service.get_current_user = AsyncMock(return_value=mock_user)

        mock_request = MagicMock()
        mock_request.cookies = {"jwt_token": "valid_token"}
        mock_request.state = MagicMock()

        result = await get_current_user_from_request(mock_request, auth_service=mock_auth_service)

        assert result["user_id"] == 1
        assert result["role"] == "STUDENT"
        assert mock_request.state.current_user_id == 1

    @pytest.mark.asyncio
    async def test_no_token_raises_401(self):
        mock_request = MagicMock()
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_request(mock_request, auth_service=MagicMock())

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        mock_auth_service = MagicMock()
        mock_auth_service.verify_token.side_effect = Exception("Invalid")
        mock_request = MagicMock()
        mock_request.cookies = {"jwt_token": "bad_token"}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_request(mock_request, auth_service=mock_auth_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_with_admin_role(self):
        mock_user = MagicMock()
        mock_auth_service = MagicMock()
        mock_auth_service.verify_token.return_value = {"sub": "1", "role": "ADMIN", "exp": 9999999999}
        mock_auth_service.get_current_user = AsyncMock(return_value=mock_user)

        mock_request = MagicMock()
        mock_request.cookies = {"jwt_token": "admin_token"}
        mock_request.state = MagicMock()

        result = await get_current_user_from_request(mock_request, auth_service=mock_auth_service)
        assert result["role"] == "ADMIN"


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_admin_success(self):
        user_data = {"user_id": 1, "role": "ADMIN", "user": MagicMock()}
        result = await require_admin(user_data)
        assert result == user_data

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        user_data = {"user_id": 1, "role": "STUDENT", "user": MagicMock()}

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "ADMIN" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_teacher_raises_403(self):
        user_data = {"user_id": 1, "role": "TEACHER", "user": MagicMock()}

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
