from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict, StrictInt


class LessonBookingBase(BaseModel):
    slot_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID слота в расписании (из таблицы LessonSlot)"
    )]
    student_id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="ID ученика (User с ролью STUDENT)"
    )]

    model_config = ConfigDict(str_strip_whitespace=True)


class LessonCreate(LessonBookingBase):
    pass


class LessonResponse(LessonBookingBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="ID записи в БД")]
    booked_at: Annotated[datetime, Field(
        ...,
        description="Дата и время создания записи"
    )]

    model_config = ConfigDict(from_attributes=True)


class LessonUpdate(BaseModel):
    slot_id: Annotated[Optional[StrictInt], Field(None, ge=1)]
    student_id: Annotated[Optional[StrictInt], Field(None, ge=1)]

    model_config = ConfigDict(str_strip_whitespace=True)