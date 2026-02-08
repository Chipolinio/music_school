from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Boolean, String, DateTime, func, ForeignKey, Text, Enum
from enum import Enum as SQLEnum
from datetime import datetime
from typing import TYPE_CHECKING

from src.models import Base

if TYPE_CHECKING:
    from .User import User


class MessageType(SQLEnum):
    INFO = "info"
    BOOKING_CONFIRM = "confirm"
    REMINDER = "reminder"
    CANCELLATION = "cancel"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[MessageType] = mapped_column(
        Enum(MessageType),
        nullable=False,
        default=MessageType.INFO
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="notifications")