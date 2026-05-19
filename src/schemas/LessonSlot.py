from typing import Annotated, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, StrictInt

from src.utils.validators import date_validator


class LessonSlotFields(BaseModel):
    """Поля слота без валидаторов ввода — для ответов API и чтения из БД."""
    teacher_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID учителя (User с ролью TEACHER)"
    )]
    room_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID комнаты"
    )]
    start_time: Annotated[datetime, Field(
        ...,
        description="Дата и время начала урока"
    )]
    end_time: Annotated[datetime, Field(
        ...,
        description="Дата и время окончания урока"
    )]
    max_participants: Annotated[StrictInt, Field(
        1,
        ge=1,
        le=20,
        description="Максимальное количество учеников в слоте"
    )]

    model_config = ConfigDict(str_strip_whitespace=True)


class LessonSlotCreate(LessonSlotFields):
    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def validate_dates(cls, v):
        """Проверяем, что дата не в прошлом (только при создании)."""
        return date_validator(v)

    @model_validator(mode="after")
    def check_time_range(self) -> "LessonSlotCreate":
        """Проверяем, что урок не заканчивается раньше, чем начался."""
        if self.end_time <= self.start_time:
            raise ValueError("Время окончания должно быть строго позже времени начала")

        duration = (self.end_time - self.start_time).total_seconds() / 60
        if duration < 30:
            raise ValueError("Урок не может длиться менее 30 минут")

        return self


class LessonSlotResponse(LessonSlotFields):
    id: Annotated[StrictInt, Field(..., ge=1, description="ID записи в БД")]

    model_config = ConfigDict(from_attributes=True)


class LessonSlotUpdate(BaseModel):
    teacher_id: Annotated[Optional[StrictInt], Field(None, ge=1)]
    room_id: Annotated[Optional[StrictInt], Field(None, ge=1)]
    start_time: Annotated[Optional[datetime], Field(None)]
    end_time: Annotated[Optional[datetime], Field(None)]
    max_participants: Annotated[Optional[StrictInt], Field(None, ge=1, le=20)]

    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def validate_dates(cls, v):
        if v is None: return v
        return date_validator(v)

    @model_validator(mode="after")
    def validate_update_range(self) -> "LessonSlotUpdate":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("Время окончания должно быть позже начала")
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


# =============================================================================
# API RESPONSES
# =============================================================================

class LessonSlotListResponse(BaseModel):
    """Список слотов уроков с пагинацией."""
    slots: Annotated[List[LessonSlotResponse], Field(..., description="Список слотов")]
    total: Annotated[int, Field(..., description="Общее количество", ge=0)]

    model_config = ConfigDict(from_attributes=True)


class LessonSlotCreateResponse(BaseModel):
    """Ответ на создание слота."""
    slot: LessonSlotResponse
    message: Annotated[str, Field(..., description="Сообщение об успехе")]

    model_config = ConfigDict(from_attributes=True)


class LessonSlotUpdateResponse(BaseModel):
    """Ответ на обновление слота."""
    slot: LessonSlotResponse
    message: Annotated[str, Field(..., description="Сообщение об успехе")]

    model_config = ConfigDict(from_attributes=True)


class LessonSlotDeleteResponse(BaseModel):
    """Ответ на удаление слота."""
    message: Annotated[str, Field(..., description="Сообщение об успехе")]