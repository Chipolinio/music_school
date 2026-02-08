from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.BaseRepository import BaseRepository
from src.models.LessonBooking import LessonBooking

class LessonBookingRepository(BaseRepository[LessonBooking]):
    def __init__(self, session: AsyncSession):
        super().__init__(LessonBooking, session)

    async def get_student_bookings(self, student_id: int):
        stmt = select(self.model).where(self.model.student_id == student_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_bookings_for_slot(self, slot_id: int) -> int:
        stmt = select(func.count(self.model.id)).where(self.model.slot_id == slot_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0