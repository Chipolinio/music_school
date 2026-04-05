from datetime import datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, StrictInt

from src.utils.validators import date_validator


class RehearsalBase(BaseModel):
    student_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID ученика (User)"
    )]
    room_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID комнаты"
    )]
    start_time: Annotated[datetime, Field(
        ...,
        description="Время начала репетиции"
    )]
    end_time: Annotated[datetime, Field(
        ...,
        description="Время окончания репетиции"
    )]

    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def validate_dates(cls, v):
        return date_validator(v)

    @model_validator(mode="after")
    def check_time_range(self) -> "RehearsalBase":
        if self.end_time <= self.start_time:
            raise ValueError("Время окончания должно быть позже начала")

        duration = (self.end_time - self.start_time).total_seconds() / 3600
        if duration < 1:
            raise ValueError("Минимальное время репетиции — 1 час")

        return self

    model_config = ConfigDict(str_strip_whitespace=True)


class RehearsalCreate(RehearsalBase):
    pass


class RehearsalResponse(BaseModel):
    id: Annotated[StrictInt, Field(..., ge=1, description="ID записи в БД")]
    student_id: Annotated[StrictInt, Field(..., ge=1, description="ID ученика")]
    room_id: Annotated[StrictInt, Field(..., ge=1, description="ID комнаты")]
    start_time: Annotated[datetime, Field(..., description="Время начала")]
    end_time: Annotated[datetime, Field(..., description="Время окончания")]
    status: Annotated[str, Field(..., description="Статус брони")]

    model_config = ConfigDict(from_attributes=True)


class RehearsalUpdate(BaseModel):
    room_id: Annotated[Optional[StrictInt], Field(None, ge=1)]
    start_time: Annotated[Optional[datetime], Field(None)]
    end_time: Annotated[Optional[datetime], Field(None)]

    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def validate_dates(cls, v):
        if v is None: return v
        return date_validator(v)

    @model_validator(mode="after")
    def validate_update_range(self) -> "RehearsalUpdate":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("Конец должен быть позже начала")
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


# =============================================================================
# API RESPONSES
# =============================================================================

class RehearsalListResponse(BaseModel):
    """Список бронирований репетиций."""
    rehearsals: Annotated[List[RehearsalResponse], Field(..., description="Список репетиций")]
    total: Annotated[int, Field(..., description="Общее количество", ge=0)]

    model_config = ConfigDict(from_attributes=True)


class RehearsalCreateResponse(BaseModel):
    """Ответ на создание бронирования репетиции."""
    rehearsal: RehearsalResponse
    message: Annotated[str, Field(..., description="Сообщение об успехе")]

    model_config = ConfigDict(from_attributes=True)


class RehearsalCancelResponse(BaseModel):
    """Ответ на отмену репетиции."""
    message: Annotated[str, Field(..., description="Сообщение об успехе")]