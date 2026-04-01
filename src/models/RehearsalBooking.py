from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, ForeignKey, Enum
from enum import Enum as SQLEnum
from datetime import datetime
from src.models.Base import BaseModel

class Status(SQLEnum):
    BOOKED = "BOOKED"
    FREE = "FREE"
    TAKEN = "TAKEN"

class RehearsalBooking(BaseModel):
    __tablename__ = "rehearsal_bookings"
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[Status] = mapped_column(
        Enum(Status),
        nullable=False,
        server_default=Status.FREE.value
    )

    student: Mapped["User"] = relationship(
        "User",
        back_populates="rehearsals"
    )
    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="rehearsal_bookings"
    )
