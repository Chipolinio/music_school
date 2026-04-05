"""
Сервис уведомлений.

Функциональный стиль: stateless функции, зависимости передаются явно.
"""

import logging
from typing import List

from src.repositories.NotificationRepository import NotificationRepository
from src.schemas.Notification import NotificationCreate, NotificationResponse
from src.models.Notification import MessageType
from src.services.exceptions import BookingNotFoundError

logger = logging.getLogger(__name__)


async def get_user_notifications(
    notification_repository: NotificationRepository,
    user_id: int,
    unread_only: bool = False,
) -> List[NotificationResponse]:
    """
    Получает уведомления пользователя.

    Args:
        notification_repository: Репозиторий уведомлений
        user_id: ID пользователя
        unread_only: Если True, возвращает только непрочитанные

    Returns:
        List[NotificationResponse]: Список уведомлений
    """
    logger.debug(f"Получение уведомлений для пользователя {user_id}, unread_only={unread_only}")

    if unread_only:
        notifications = await notification_repository.get_unread(user_id)
    else:
        notifications = await notification_repository.get_all()
        notifications = [n for n in notifications if n.user_id == user_id]

    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]


async def mark_as_read(
    notification_repository: NotificationRepository,
    notification_id: int,
    user_id: int,
) -> None:
    """
    Помечает уведомление как прочитанное.

    Args:
        notification_repository: Репозиторий уведомлений
        notification_id: ID уведомления
        user_id: ID пользователя (для проверки прав)

    Raises:
        BookingNotFoundError: если уведомление не найдено
    """
    logger.debug(f"Пометка уведомления {notification_id} как прочитанного")

    notification = await notification_repository.get_by_id(notification_id)
    if notification is None:
        logger.warning(f"Уведомление с ID {notification_id} не найдено")
        raise BookingNotFoundError(notification_id)

    if notification.user_id != user_id:
        logger.warning(
            f"Пользователь {user_id} попытался прочитать чужое уведомление {notification_id}"
        )
        raise BookingNotFoundError(notification_id)

    notification.is_read = True
    await notification_repository.update(notification)
    await notification_repository.session.commit()
    logger.info(f"Уведомление {notification_id} помечено как прочитанное")


async def mark_all_as_read(
    notification_repository: NotificationRepository,
    user_id: int,
) -> None:
    """
    Помечает все уведомления пользователя как прочитанные.

    Args:
        notification_repository: Репозиторий уведомлений
        user_id: ID пользователя
    """
    logger.debug(f"Пометка всех уведомлений пользователя {user_id} как прочитанных")

    await notification_repository.mark_all_as_read(user_id)
    await notification_repository.session.commit()
    logger.info(f"Все уведомления пользователя {user_id} помечены как прочитанные")


async def create_notification(
    notification_repository: NotificationRepository,
    notification_data: NotificationCreate,
) -> NotificationResponse:
    """
    Создаёт новое уведомление.

    Args:
        notification_repository: Репозиторий уведомлений
        notification_data: Данные уведомления

    Returns:
        NotificationResponse: Данные созданного уведомления
    """
    logger.debug(f"Создание уведомления для пользователя {notification_data.user_id}")

    created_notification = await notification_repository.create_notification(
        user_id=notification_data.user_id,
        title=notification_data.title,
        message=notification_data.message,
        msg_type=notification_data.type.value if hasattr(notification_data, 'type') and notification_data.type else "info",
        is_read=notification_data.is_read,
    )
    await notification_repository.session.commit()
    logger.info(f"Уведомление {created_notification.id} успешно создано")

    return NotificationResponse(
        id=created_notification.id,
        user_id=created_notification.user_id,
        title=created_notification.title,
        message=created_notification.message,
        is_read=created_notification.is_read,
        created_at=created_notification.created_at,
    )
