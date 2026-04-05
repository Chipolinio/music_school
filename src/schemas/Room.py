from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, StrictInt

from src.utils.validators import generic_name_validator


class RoomBase(BaseModel):
    name: Annotated[str, Field(
        ...,
        min_length=2,
        max_length=50,
        description="Название музыкального класса/зала",
        examples=["Зал ударных", "Класс фортепиано"]
    )]
    capacity: Annotated[StrictInt, Field(
        3,
        ge=1,
        le=100,
        description="Вместимость (человек)"
    )]
    is_active: Annotated[bool, Field(
        True,
        description="Статус доступности зала"
    )]

    @field_validator("name", mode="after")
    @classmethod
    def validate_room_name(cls, v):
        return generic_name_validator(v)

    model_config = ConfigDict(str_strip_whitespace=True)


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID записи")]

    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    name: Annotated[Optional[str], Field(
        None,
        min_length=2,
        max_length=50
    )]
    capacity: Annotated[Optional[StrictInt], Field(None, ge=1, le=100)]
    is_active: Annotated[Optional[bool], Field(None)]

    @field_validator("name", mode="after")
    @classmethod
    def validate_room_name(cls, v):
        if v is None:
            return v
        return generic_name_validator(v)

    model_config = ConfigDict(str_strip_whitespace=True)


# =============================================================================
# API RESPONSES
# =============================================================================

class RoomListResponse(BaseModel):
    """Список комнат с пагинацией."""
    rooms: Annotated[List[RoomResponse], Field(..., description="Список комнат")]
    total: Annotated[int, Field(..., description="Общее количество", ge=0)]

    model_config = ConfigDict(from_attributes=True)


class RoomCreateResponse(BaseModel):
    """Ответ на создание комнаты."""
    room: RoomResponse
    message: Annotated[str, Field(..., description="Сообщение об успехе")]

    model_config = ConfigDict(from_attributes=True)


class RoomUpdateResponse(BaseModel):
    """Ответ на обновление комнаты."""
    room: RoomResponse
    message: Annotated[str, Field(..., description="Сообщение об успехе")]

    model_config = ConfigDict(from_attributes=True)


class RoomDeleteResponse(BaseModel):
    """Ответ на удаление комнаты."""
    message: Annotated[str, Field(..., description="Сообщение об успехе")]