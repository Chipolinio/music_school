from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, func, ForeignKey, Enum
from datetime import datetime
from enum import Enum as SQLEnum

from src.models.Base import BaseModel


class Status(SQLEnum):
    BOOKED = "BOOKED"
    FREE = "FREE"
    TAKEN = "TAKEN"


class LessonBooking(BaseModel):
    __tablename__ = "lesson_bookings"
    slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lesson_slots.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[Status] = mapped_column(
        Enum(Status),
        nullable=False,
        server_default=Status.BOOKED.value)
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    slot: Mapped["LessonSlot"] = relationship("LessonSlot", back_populates="lesson_bookings") # Было lesson_slots
    student: Mapped["User"] = relationship("User", back_populates="lesson_bookings") # Было user