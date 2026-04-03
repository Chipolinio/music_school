"""
API роуты для уведомлений.
"""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_notification_service, NotificationService
from src.schemas.Notification import NotificationResponse, NotificationCreate, NotificationListResponse, NotificationCreateResponse, NotificationMarkAsReadResponse, NotificationMarkAllAsReadResponse


router = APIRouter(prefix="/notifications", tags=["Уведомления"])


@router.get("/user/{user_id}", response_model=NotificationListResponse)
async def get_user_notifications(
    user_id: int,
    unread_only: bool = False,
    service: NotificationService = Depends(get_notification_service),
):
    """Получение уведомлений пользователя."""
    notifications = await service.get_user(user_id, unread_only)
    unread_count = sum(1 for n in notifications if not n.is_read)
    return NotificationListResponse(notifications=notifications, unread_count=unread_count)


@router.post("/{notification_id}/mark-as-read", response_model=NotificationMarkAsReadResponse)
async def mark_as_read(
    notification_id: int,
    user_id: int,
    service: NotificationService = Depends(get_notification_service),
):
    """Пометить уведомление как прочитанное."""
    await service.mark_as_read(notification_id, user_id)
    return NotificationMarkAsReadResponse(message="Уведомление помечено как прочитанное")


@router.post("/user/{user_id}/mark-all-as-read", response_model=NotificationMarkAllAsReadResponse)
async def mark_all_as_read(
    user_id: int,
    service: NotificationService = Depends(get_notification_service),
):
    """Пометить все уведомления пользователя как прочитанные."""
    await service.mark_all_as_read(user_id)
    return NotificationMarkAllAsReadResponse(message="Все уведомления помечены как прочитанные")


@router.post("/", response_model=NotificationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
):
    """Создание уведомления."""
    notification = await service.create(notification_data)
    return NotificationCreateResponse(notification=notification, message="Уведомление успешно создано")
