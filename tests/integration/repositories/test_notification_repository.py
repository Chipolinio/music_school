"""
Тесты для NotificationRepository.

Покрывает методы: create_notification, get_unread, mark_all_as_read.

Чеклист (раздел 5.7):
| Метод | Тест |
|-------|------|
| `create_notification` | Создание с MessageType |
| `get_unread` | Только непрочитанные |
| `mark_all_as_read` | Bulk update, все стали is_read=True |
"""

import pytest

from src.models.User import User, UserRole
from src.models.Notification import Notification, MessageType
from src.repositories.NotificationRepository import NotificationRepository


class TestNotificationRepositoryCreateNotification:
    """Тесты метода create_notification."""

    @pytest.mark.asyncio
    async def test_create_notification(self, session, student):
        """Тест создания уведомления."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Тест",
            message="Тестовое сообщение",
            msg_type="info",
            is_read=False,
        )

        assert notification.id is not None
        assert notification.user_id == student.id
        assert notification.title == "Тест"
        assert notification.message == "Тестовое сообщение"
        assert notification.type == MessageType.INFO
        assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_create_notification_booking_confirm(self, session, student):
        """Тест создания уведомления с типом BOOKING_CONFIRM."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Подтверждение",
            message="Бронирование подтверждено",
            msg_type="confirm",
        )

        assert notification.type == MessageType.BOOKING_CONFIRM

    @pytest.mark.asyncio
    async def test_create_notification_reminder(self, session, student):
        """Тест создания уведомления с типом REMINDER."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Напоминание",
            message="Напоминание о уроке",
            msg_type="reminder",
        )

        assert notification.type == MessageType.REMINDER

    @pytest.mark.asyncio
    async def test_create_notification_cancellation(self, session, student):
        """Тест создания уведомления с типом CANCELLATION."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Отмена",
            message="Урок отменён",
            msg_type="cancel",
        )

        assert notification.type == MessageType.CANCELLATION

    @pytest.mark.asyncio
    async def test_create_notification_system(self, session, student):
        """Тест создания уведомления с типом SYSTEM."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Системное",
            message="Системное сообщение",
            msg_type="system",
        )

        assert notification.type == MessageType.SYSTEM

    @pytest.mark.asyncio
    async def test_create_notification_default_is_read(self, session, student):
        """Тест: is_read=False по умолчанию."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Тест",
            message="Сообщение",
            msg_type="info",
        )

        assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_create_notification_is_read_true(self, session, student):
        """Тест создания прочитанного уведомления."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Тест",
            message="Сообщение",
            msg_type="info",
            is_read=True,
        )

        assert notification.is_read is True

    @pytest.mark.asyncio
    async def test_create_notification_returns_instance(self, session, student):
        """create_notification возвращает тот же экземпляр."""
        repo = NotificationRepository(session)

        notification = await repo.create_notification(
            user_id=student.id,
            title="Тест",
            message="Сообщение",
            msg_type="info",
        )

        assert isinstance(notification, Notification)
        assert notification.id is not None


class TestNotificationRepositoryGetUnread:
    """Тесты метода get_unread."""

    @pytest.mark.asyncio
    async def test_get_unread(self, session, student):
        """Тест получения непрочитанных."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="Непрочитанное", message="msg1", msg_type="info", is_read=False)
        await repo.create_notification(user_id=student.id, title="Прочитанное", message="msg2", msg_type="info", is_read=True)

        unread = await repo.get_unread(student.id)
        assert len(unread) == 1
        assert unread[0].title == "Непрочитанное"
        assert unread[0].is_read is False

    @pytest.mark.asyncio
    async def test_get_unread_all_unread(self, session, student):
        """Тест: все уведомления непрочитанные."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="1", message="msg1", is_read=False)
        await repo.create_notification(user_id=student.id, title="2", message="msg2", is_read=False)
        await repo.create_notification(user_id=student.id, title="3", message="msg3", is_read=False)

        unread = await repo.get_unread(student.id)
        assert len(unread) == 3

    @pytest.mark.asyncio
    async def test_get_unread_all_read(self, session, student):
        """Тест: все уведомления прочитанные — пустой список."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="1", message="msg1", is_read=True)
        await repo.create_notification(user_id=student.id, title="2", message="msg2", is_read=True)

        unread = await repo.get_unread(student.id)
        assert len(unread) == 0

    @pytest.mark.asyncio
    async def test_get_unread_empty(self, session, student):
        """Тест: нет уведомлений."""
        repo = NotificationRepository(session)

        unread = await repo.get_unread(student.id)
        assert len(unread) == 0

    @pytest.mark.asyncio
    async def test_get_unread_different_users(self, session, student, teacher):
        """Тест: непрочитанные только для конкретного пользователя."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="Студент", message="msg1", is_read=False)
        await repo.create_notification(user_id=teacher.id, title="Преподаватель", message="msg2", is_read=False)

        student_unread = await repo.get_unread(student.id)
        teacher_unread = await repo.get_unread(teacher.id)

        assert len(student_unread) == 1
        assert student_unread[0].title == "Студент"
        assert len(teacher_unread) == 1
        assert teacher_unread[0].title == "Преподаватель"


class TestNotificationRepositoryMarkAllAsRead:
    """Тесты метода mark_all_as_read."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, session, student):
        """Тест: mark_all_as_read — bulk update."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="1", message="msg1", is_read=False)
        await repo.create_notification(user_id=student.id, title="2", message="msg2", is_read=False)
        await repo.create_notification(user_id=student.id, title="3", message="msg3", is_read=False)

        await repo.mark_all_as_read(student.id)

        unread = await repo.get_unread(student.id)
        assert len(unread) == 0

    @pytest.mark.asyncio
    async def test_mark_all_as_read_only_unread(self, session, student):
        """Тест: mark_all_as_read не трогает уже прочитанные."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="1", message="msg1", is_read=False)
        await repo.create_notification(user_id=student.id, title="2", message="msg2", is_read=True)

        await repo.mark_all_as_read(student.id)

        all_notifs = await repo.get_all()
        for n in all_notifs:
            assert n.is_read is True

    @pytest.mark.asyncio
    async def test_mark_all_as_read_no_unread(self, session, student):
        """Тест: нет непрочитанных — ничего не меняется."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="1", message="msg1", is_read=True)
        await repo.create_notification(user_id=student.id, title="2", message="msg2", is_read=True)

        await repo.mark_all_as_read(student.id)

        all_notifs = await repo.get_all()
        assert len(all_notifs) == 2
        for n in all_notifs:
            assert n.is_read is True

    @pytest.mark.asyncio
    async def test_mark_all_as_read_empty(self, session, student):
        """Тест: нет уведомлений — ошибка не возникает."""
        repo = NotificationRepository(session)

        await repo.mark_all_as_read(student.id)

        unread = await repo.get_unread(student.id)
        assert len(unread) == 0

    @pytest.mark.asyncio
    async def test_mark_all_as_read_different_users(self, session, student, teacher):
        """Тест: mark_all_as_read только для указанного пользователя."""
        repo = NotificationRepository(session)

        await repo.create_notification(user_id=student.id, title="Студент", message="msg1", is_read=False)
        await repo.create_notification(user_id=teacher.id, title="Преподаватель", message="msg2", is_read=False)

        await repo.mark_all_as_read(student.id)

        student_unread = await repo.get_unread(student.id)
        teacher_unread = await repo.get_unread(teacher.id)

        assert len(student_unread) == 0
        assert len(teacher_unread) == 1
