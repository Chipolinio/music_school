from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, String, SmallInteger
from typing import List

from src.models.Base import BaseModel

class Room(BaseModel):
    __tablename__ = "rooms"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    lesson_slots: Mapped[List["LessonSlot"]] = relationship(
        "LessonSlot", back_populates="room", cascade="all, delete-orphan"
    )
    rehearsal_bookings: Mapped[List["RehearsalBooking"]] = relationship(
        "RehearsalBooking", back_populates="room", cascade="all, delete-orphan"
    )