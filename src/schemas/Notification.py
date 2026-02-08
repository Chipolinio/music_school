from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict, StrictInt


class NotificationBase(BaseModel):
    user_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID пользователя, которому пришло уведомление"
    )]
    text: Annotated[str, Field(
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