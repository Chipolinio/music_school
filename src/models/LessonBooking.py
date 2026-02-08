from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, func, ForeignKey
from datetime import datetime

from src.models import Base

class LessonBooking(Base):
    __tablename__ = "lesson_bookings"
    slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lesson_slots.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False, server_default="booked")
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    slot: Mapped["LessonSlot"] = relationship("LessonSlot", back_populates="lesson_bookings") # Было lesson_slots
    student: Mapped["User"] = relationship("User", back_populates="lesson_bookings") # Было user