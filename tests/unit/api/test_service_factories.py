"""
Unit-тесты для фабрик сервисов (deps.py).
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.api.deps import (
    AuthService, UserService, RoomService,
    ScheduleService, BookingService, RehearsalService,
    NotificationService, ReportService,
    get_auth_service, get_user_service, get_room_service,
    get_schedule_service, get_booking_service, get_rehearsal_service,
    get_notification_service, get_report_service,
)


class TestServiceFactories:
    def test_get_auth_service(self):
        result = get_auth_service(MagicMock())
        assert isinstance(result, AuthService)

    def test_get_user_service(self):
        result = get_user_service(MagicMock())
        assert isinstance(result, UserService)

    def test_get_room_service(self):
        result = get_room_service(MagicMock())
        assert isinstance(result, RoomService)

    def test_get_schedule_service(self):
        result = get_schedule_service(MagicMock())
        assert isinstance(result, ScheduleService)

    def test_get_booking_service(self):
        result = get_booking_service(MagicMock())
        assert isinstance(result, BookingService)

    def test_get_rehearsal_service(self):
        result = get_rehearsal_service(MagicMock())
        assert isinstance(result, RehearsalService)

    def test_get_notification_service(self):
        result = get_notification_service(MagicMock())
        assert isinstance(result, NotificationService)

    def test_get_report_service(self):
        result = get_report_service(MagicMock())
        assert isinstance(result, ReportService)


class TestAuthService:
    def test_init(self):
        service = AuthService(MagicMock())
        assert service.user_repo is not None

    @pytest.mark.asyncio
    async def test_register(self):
        service = AuthService(MagicMock())
        mock_user, mock_token = MagicMock(), "token"
        with patch("src.api.deps.auth_service.register", new_callable=AsyncMock) as m:
            m.return_value = (mock_user, mock_token)
            u, t = await service.register(MagicMock())
            assert t == mock_token

    @pytest.mark.asyncio
    async def test_login(self):
        service = AuthService(MagicMock())
        mock_user, mock_token = MagicMock(), "token"
        with patch("src.api.deps.auth_service.login", new_callable=AsyncMock) as m:
            m.return_value = (mock_user, mock_token)
            u, t = await service.login("+79991234567", "pass")
            assert t == mock_token

    def test_logout(self):
        service = AuthService(MagicMock())
        with patch("src.api.deps.auth_service.logout") as m:
            service.logout("token")
            m.assert_called_once_with("token")


class TestUserService:
    def test_init(self):
        service = UserService(MagicMock())
        assert service.user_repo is not None

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        service = UserService(MagicMock())
        mock_user = MagicMock()
        with patch("src.api.deps.user_service.get_user_by_id", new_callable=AsyncMock) as m:
            m.return_value = mock_user
            result = await service.get_by_id(1)
            assert result == mock_user


class TestRoomService:
    def test_init(self):
        service = RoomService(MagicMock())
        assert service.room_repo is not None


class TestScheduleService:
    def test_init(self):
        service = ScheduleService(MagicMock())
        assert service.slot_repo is not None
        assert service.user_repo is not None
        assert service.room_repo is not None


class TestBookingService:
    def test_init(self):
        service = BookingService(MagicMock())
        assert service.booking_repo is not None
        assert service.slot_repo is not None


class TestRehearsalService:
    def test_init(self):
        service = RehearsalService(MagicMock())
        assert service.rehearsal_repo is not None
        assert service.slot_repo is not None


class TestNotificationService:
    def test_init(self):
        service = NotificationService(MagicMock())
        assert service.notification_repo is not None


class TestReportService:
    def test_init(self):
        service = ReportService(MagicMock())
        assert service.booking_repo is not None
        assert service.slot_repo is not None
