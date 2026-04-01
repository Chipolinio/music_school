from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer,SmallInteger, DateTime, ForeignKey, Enum
from enum import Enum as SQLEnum
from datetime import datetime
from typing import List

from src.models.Base import BaseModel


class LessonType(SQLEnum):
    TRIAL = "TRIAL"
    LESSON = "LESSON"


class LessonSlot(BaseModel):
    __tablename__ = "lesson_slots"
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # Исправлено
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    max_participants: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), nullable=False,
                                                    server_default=LessonType.LESSON.value)

    lesson_bookings: Mapped[List["LessonBooking"]] = relationship("LessonBooking", back_populates="slot")  # Исправлено
    teacher: Mapped["User"] = relationship("User", back_populates="teacher_slots")
    room: Mapped["Room"] = relationship("Room", back_populates="lesson_slots")


