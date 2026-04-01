from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, String, DateTime, func, Enum
from enum import Enum as SQLEnum
from datetime import datetime
from typing import List

from src.models.Base import BaseModel

class UserRole(SQLEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"


class User(BaseModel):
    __tablename__ = "users"
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        server_default=UserRole.STUDENT.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    teacher_slots: Mapped[List["LessonSlot"]] = relationship(
        "LessonSlot",
        back_populates="teacher",
        cascade = "all, delete-orphan"
    )
    lesson_bookings: Mapped[List["LessonBooking"]] = relationship(
        "LessonBooking",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    rehearsals: Mapped[List["RehearsalBooking"]] = relationship(
        "RehearsalBooking",
        back_populates="student",
        cascade="all, delete-orphan"
    )

