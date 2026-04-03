from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy import select, func, extract, case, cast, Date, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.repositories.BaseRepository import BaseRepository
from src.models.LessonBooking import LessonBooking, Status
from src.models.LessonSlot import LessonSlot


class LessonBookingRepository(BaseRepository[LessonBooking]):
    def __init__(self, session: AsyncSession):
        super().__init__(LessonBooking, session)

    async def create_booking(
        self,
        slot_id: int,
        student_id: int,
        status: str = "BOOKED",
    ) -> LessonBooking:
        """Создаёт бронирование урока."""
        booking = self.model(
            slot_id=slot_id,
            student_id=student_id,
            status=Status(status),
        )
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)
        return booking

    async def get_student_bookings(self, student_id: int) -> List[LessonBooking]:
        """Все брони студента."""
        stmt = select(self.model).where(self.model.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_student_active_bookings(self, student_id: int) -> List[LessonBooking]:
        """Все активные брони студента (со статусом BOOKED)."""
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                text("lesson_bookings.status = 'BOOKED'")
            )
            .options(selectinload(self.model.slot))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_bookings_for_slot(self, slot_id: int) -> int:
        """Количество записей в слот."""
        stmt = select(func.count(self.model.id)).where(
            self.model.slot_id == slot_id,
            text("lesson_bookings.status = 'BOOKED'")
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_booking_with_slot(self, booking_id: int) -> Optional[LessonBooking]:
        """Бронь с данными слота (JOIN)."""
        stmt = (
            select(self.model)
            .options(selectinload(self.model.slot))
            .where(self.model.id == booking_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_lesson_count_by_teacher(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Количество уроков по преподавателям за период (JOIN с LessonSlot, GROUP BY teacher_id)."""
        stmt = (
            select(
                LessonSlot.teacher_id,
                func.count(self.model.id).label("lesson_count")
            )
            .join(LessonSlot, self.model.slot_id == LessonSlot.id)
            .where(
                func.date(LessonSlot.start_time) >= cast(start_date, Date),
                func.date(LessonSlot.start_time) <= cast(end_date, Date)
            )
            .group_by(LessonSlot.teacher_id)
        )
        result = await self.session.execute(stmt)
        return [
            {"teacher_id": row.teacher_id, "lesson_count": row.lesson_count}
            for row in result.all()
        ]

    async def get_user_attendance_stats(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Статистика посещаемости пользователя.
        Возвращает COUNT и SUM с CASE для подсчёта посещённых и забронированных уроков.
        """
        stmt = (
            select(
                func.count(self.model.id).label("total_lessons"),
                func.sum(
                    case(
                        (text("lesson_bookings.status = 'BOOKED'"), 1),
                        else_=0
                    )
                ).label("booked"),
                func.sum(
                    case(
                        (text("lesson_bookings.status = 'TAKEN'"), 1),
                        else_=0
                    )
                ).label("attended")
            )
            .join(LessonSlot, self.model.slot_id == LessonSlot.id)
            .where(
                self.model.student_id == user_id,
                func.date(LessonSlot.start_time) >= cast(start_date, Date),
                func.date(LessonSlot.start_time) <= cast(end_date, Date)
            )
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if row is None:
            return {
                "total_lessons": 0,
                "booked": 0,
                "attended": 0
            }
        return {
            "total_lessons": row.total_lessons or 0,
            "booked": row.booked or 0,
            "attended": row.attended or 0
        }

    async def get_peak_hours(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Популярные часы для уроков.
        EXTRACT hour, GROUP BY, ORDER BY.
        """
        stmt = (
            select(
                extract("hour", LessonSlot.start_time).label("hour"),
                func.count(self.model.id).label("slot_count")
            )
            .join(LessonSlot, self.model.slot_id == LessonSlot.id)
            .where(
                func.date(LessonSlot.start_time) >= cast(start_date, Date),
                func.date(LessonSlot.start_time) <= cast(end_date, Date)
            )
            .group_by(extract("hour", LessonSlot.start_time))
            .order_by(func.count(self.model.id).desc())
        )
        result = await self.session.execute(stmt)
        return [
            {"hour": int(row.hour), "slot_count": row.slot_count}
            for row in result.all()
        ]