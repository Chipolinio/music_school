"""
Unit-тесты сервиса уведомлений.

Тестируются: get_user_notifications, mark_as_read, mark_all_as_read, create_notification
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.notification import (
    get_user_notifications, mark_as_read, mark_all_as_read, create_notification,
)
from src.schemas.Notification import NotificationCreate, NotificationResponse
from src.models.Notification import MessageType
from src.services.exceptions import BookingNotFoundError


class TestGetUserNotifications:
    """Тесты функции get_user_notifications."""

    @pytest.mark.asyncio
    async def test_get_all_notifications(self, mock_notification_repo, mock_notification_model):
        """Тест получения всех уведомлений."""
        mock_notification_model.user_id = 1
        mock_notification_repo.get_all.return_value = [mock_notification_model]

        result = await get_user_notifications(mock_notification_repo, user_id=1, unread_only=False)

        assert len(result) == 1
        assert result[0].user_id == 1

    @pytest.mark.asyncio
    async def test_get_unread_only(self, mock_notification_repo):
        """Тест получения только непрочитанных."""
        unread = MagicMock()
        unread.id = 1
        unread.user_id = 1
        unread.title = "Непрочитанное"
        unread.message = "Сообщение"
        unread.is_read = False
        unread.created_at = MagicMock()

        mock_notification_repo.get_unread.return_value = [unread]

        result = await get_user_notifications(mock_notification_repo, user_id=1, unread_only=True)

        assert len(result) == 1
        assert result[0].is_read is False
        mock_notification_repo.get_unread.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_notifications_filters_by_user(self, mock_notification_repo):
        """Тест что get_all фильтрует по user_id."""
        notif1 = MagicMock()
        notif1.user_id = 1
        notif1.id = 1
        notif1.title = "Для юзера 1"
        notif1.message = "Сообщение"
        notif1.is_read = False
        notif1.created_at = MagicMock()

        notif2 = MagicMock()
        notif2.user_id = 2
        notif2.id = 2
        notif2.title = "Для юзера 2"
        notif2.message = "Сообщение"
        notif2.is_read = False
        notif2.created_at = MagicMock()

        mock_notification_repo.get_all.return_value = [notif1, notif2]

        result = await get_user_notifications(mock_notification_repo, user_id=1, unread_only=False)

        assert len(result) == 1
        assert result[0].user_id == 1

    @pytest.mark.asyncio
    async def test_get_notifications_empty(self, mock_notification_repo):
        """Тест пустого списка."""
        mock_notification_repo.get_all.return_value = []

        result = await get_user_notifications(mock_notification_repo, user_id=1)

        assert result == []


class TestMarkAsRead:
    """Тесты функции mark_as_read."""

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, mock_notification_repo, mock_notification_model):
        """Тест успешной пометки как прочитанное."""
        mock_notification_repo.get_by_id.return_value = mock_notification_model

        await mark_as_read(mock_notification_repo, notification_id=1, user_id=1)

        assert mock_notification_model.is_read is True
        mock_notification_repo.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, mock_notification_repo):
        """Тест когда уведомление не найдено."""
        mock_notification_repo.get_by_id.return_value = None

        with pytest.raises(BookingNotFoundError):
            await mark_as_read(mock_notification_repo, notification_id=999, user_id=1)

    @pytest.mark.asyncio
    async def test_mark_as_read_wrong_user(self, mock_notification_repo, mock_notification_model):
        """Тест: пользователь не может пометить чужое уведомление."""
        mock_notification_model.user_id = 1
        mock_notification_repo.get_by_id.return_value = mock_notification_model

        with pytest.raises(BookingNotFoundError):
            await mark_as_read(mock_notification_repo, notification_id=1, user_id=999)


class TestMarkAllAsRead:
    """Тесты функции mark_all_as_read."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, mock_notification_repo):
        """Тест пометки всех уведомлений."""
        await mark_all_as_read(mock_notification_repo, user_id=1)

        mock_notification_repo.mark_all_as_read.assert_called_once_with(1)
        mock_notification_repo.session.commit.assert_called_once()


class TestCreateNotification:
    """Тесты функции create_notification."""

    @pytest.mark.asyncio
    async def test_create_notification_success(self, mock_notification_repo, notification_create_data):
        """Тест успешного создания уведомления."""
        created = MagicMock()
        created.id = 1
        created.user_id = 1
        created.title = "Тестовое уведомление"
        created.message = "Тестовое сообщение"
        created.is_read = False
        created.created_at = MagicMock()
        mock_notification_repo.create_notification.return_value = created

        response = await create_notification(mock_notification_repo, notification_create_data)

        assert isinstance(response, NotificationResponse)
        assert response.user_id == 1
        assert response.title == "Тестовое уведомление"
        mock_notification_repo.session.commit.assert_called_once()
