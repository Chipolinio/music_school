from datetime import datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict, StrictInt


class NotificationBase(BaseModel):
    user_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID пользователя, которому пришло уведомление"
    )]
    title: Annotated[str, Field(
        ...,
        min_length=1,
        max_length=150,
        description="Заголовок уведомления"
    )]
    message: Annotated[str, Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Текст уведомления"
    )]
    is_read: Annotated[bool, Field(
        False,
        description="Статус прочтения (True — прочитано)"
    )]

    model_config = ConfigDict(str_strip_whitespace=True)


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="ID записи в БД")]
    created_at: Annotated[datetime, Field(
        ...,
        description="Дата и время отправки уведомления"
    )]

    model_config = ConfigDict(from_attributes=True)


class NotificationUpdate(BaseModel):
    is_read: Annotated[Optional[bool], Field(None)]

    model_config = ConfigDict(str_strip_whitespace=True)


# =============================================================================
# API RESPONSES
# =============================================================================

class NotificationListResponse(BaseModel):
    """Список уведомлений."""
    notifications: Annotated[List[NotificationResponse], Field(..., description="Список уведомлений")]
    unread_count: Annotated[int, Field(..., description="Количество непрочитанных", ge=0)]

    model_config = ConfigDict(from_attributes=True)


class NotificationCreateResponse(BaseModel):
    """Ответ на создание уведомления."""
    notification: NotificationResponse
    message: Annotated[str, Field(..., description="Сообщение об успехе")]

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkAsReadResponse(BaseModel):
    """Ответ на пометку уведомления как прочитанного."""
    message: Annotated[str, Field(..., description="Сообщение об успехе")]


class NotificationMarkAllAsReadResponse(BaseModel):
    """Ответ на пометку всех уведомлений как прочитанных."""
    message: Annotated[str, Field(..., description="Сообщение об успехе")]