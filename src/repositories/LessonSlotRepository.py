from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional

from src.repositories.BaseRepository import BaseRepository
from src.models.LessonSlot  import LessonSlot


class LessonSlotRepository(BaseRepository[LessonSlot]):
    def __init__(self, session: AsyncSession):
        super().__init__(LessonSlot, session)

    async def find_conflicts(self, room_id: int, start_time: datetime, end_time: datetime):
        stmt = select(self.model).where(
            and_(
                self.model.room_id == room_id,
                self.model.start_time < end_time,
                self.model.end_time > start_time
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_teacher(self, teacher_id: int):
        stmt = select(self.model).where(self.model.teacher_id == teacher_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_for_period(self, start_date: date, end_date: Optional[date] = None):
        if end_date is None:
            stmt = select(self.model).where(func.date(self.model.start_time) == start_date)
        else:
            stmt = select(self.model).where(
                and_(
                    func.date(self.model.start_time) >= start_date,
                    func.date(self.model.start_time) <= end_date
                )
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()