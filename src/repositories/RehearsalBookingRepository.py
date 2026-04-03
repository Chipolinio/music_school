from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.BaseRepository import BaseRepository
from src.models.RehearsalBooking import RehearsalBooking, Status


class RehearsalRepository(BaseRepository[RehearsalBooking]):
    def __init__(self, session: AsyncSession):
        super().__init__(RehearsalBooking, session)

    async def create_rehearsal(
        self,
        student_id: int,
        room_id: int,
        start_time: datetime,
        end_time: datetime,
        status: str = "BOOKED",
    ) -> RehearsalBooking:
        """Создаёт бронирование репетиции."""
        booking = self.model(
            student_id=student_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            status=Status(status),
        )
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)
        return booking

    async def find_room_conflicts(
        self,
        room_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[int] = None
    ) -> List[RehearsalBooking]:
        """
        Репетиции, пересекающиеся по времени для данной комнаты.
        """
        conditions = [
            self.model.room_id == room_id,
            self.model.start_time < end_time,
            self.model.end_time > start_time,
            text("rehearsal_bookings.status = 'BOOKED'")
        ]
        if exclude_booking_id is not None:
            conditions.append(self.model.id != exclude_booking_id)
        stmt = select(self.model).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_student_conflicts(
        self,
        student_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[int] = None
    ) -> List[RehearsalBooking]:
        """
        Репетиции студента, пересекающиеся по времени.
        """
        conditions = [
            self.model.student_id == student_id,
            self.model.start_time < end_time,
            self.model.end_time > start_time,
            text("rehearsal_bookings.status = 'BOOKED'")
        ]
        if exclude_booking_id is not None:
            conditions.append(self.model.id != exclude_booking_id)
        stmt = select(self.model).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_student_rehearsals(self, student_id: int) -> List[RehearsalBooking]:
        """Все репетиции студента."""
        stmt = select(self.model).where(self.model.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
