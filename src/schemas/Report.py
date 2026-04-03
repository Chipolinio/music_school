"""
Схемы для отчётов API.
"""

from typing import Annotated, List
from pydantic import BaseModel, Field, ConfigDict, StrictInt


class LessonCountByTeacherResponse(BaseModel):
    """Отчёт по количеству уроков по преподавателям."""
    teacher_id: Annotated[StrictInt, Field(
        ...,
        gt=0,
        description="ID преподавателя"
    )]
    teacher_name: Annotated[str, Field(
        ...,
        description="ФИО преподавателя"
    )]
    lesson_count: Annotated[int, Field(
        ...,
        ge=0,
        description="Количество уроков"
    )]

    model_config = ConfigDict(from_attributes=True)


class UserAttendanceResponse(BaseModel):
    """Отчёт по посещаемости пользователя."""
    user_id: Annotated[StrictInt, Field(
        ...,
        gt=0,
        description="ID пользователя"
    )]
    user_name: Annotated[str, Field(
        ...,
        description="ФИО пользователя"
    )]
    period: Annotated[str, Field(
        ...,
        description="Период отчёта",
        examples=["2026-01-01 - 2026-01-31"]
    )]
    total_lessons: Annotated[int, Field(
        ...,
        ge=0,
        description="Всего уроков"
    )]
    booked: Annotated[int, Field(
        ...,
        ge=0,
        description="Забронировано"
    )]
    attended: Annotated[int, Field(
        ...,
        ge=0,
        description="Посещено"
    )]

    model_config = ConfigDict(from_attributes=True)


class PeakHoursResponse(BaseModel):
    """Отчёт по популярным часам."""
    hour: Annotated[int, Field(
        ...,
        ge=0,
        le=23,
        description="Час суток"
    )]
    slot_count: Annotated[int, Field(
        ...,
        ge=0,
        description="Количество слотов"
    )]

    model_config = ConfigDict(from_attributes=True)


class ReportPeriodRequest(BaseModel):
    """Запрос отчёта за период."""
    start_date: Annotated[str, Field(
        ...,
        description="Дата начала периода",
        examples=["2026-01-01"]
    )]
    end_date: Annotated[str, Field(
        ...,
        description="Дата окончания периода",
        examples=["2026-01-31"]
    )]

    model_config = ConfigDict(from_attributes=True)
