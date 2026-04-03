from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, date

from src.repositories.BaseRepository import BaseRepository
from src.models.LessonSlot import LessonSlot, LessonType


class LessonSlotRepository(BaseRepository[LessonSlot]):
    def __init__(self, session: AsyncSession):
        super().__init__(LessonSlot, session)

    async def create_slot(
        self,
        teacher_id: int,
        room_id: int,
        start_time: datetime,
        end_time: datetime,
        max_participants: int = 1,
        lesson_type: str = "LESSON",
    ) -> LessonSlot:
        """Создаёт слот урока."""
        slot = self.model(
            teacher_id=teacher_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            max_participants=max_participants,
            lesson_type=LessonType(lesson_type),
        )
        self.session.add(slot)
        await self.session.flush()
        await self.session.refresh(slot)
        return slot

    async def find_conflicts(
        self,
        room_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_slot_id: Optional[int] = None
    ) -> List[LessonSlot]:
        """Возвращает список слотов, пересекающихся по времени с указанным интервалом для данной комнаты."""
        conditions = [
            self.model.room_id == room_id,
            self.model.start_time < end_time,
            self.model.end_time > start_time
        ]
        if exclude_slot_id is not None:
            conditions.append(self.model.id != exclude_slot_id)
        stmt = select(self.model).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_teacher_conflicts(
        self,
        teacher_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_slot_id: Optional[int] = None
    ) -> List[LessonSlot]:
        """Возвращает список слотов преподавателя, пересекающихся по времени."""
        conditions = [
            self.model.teacher_id == teacher_id,
            self.model.start_time < end_time,
            self.model.end_time > start_time
        ]
        if exclude_slot_id is not None:
            conditions.append(self.model.id != exclude_slot_id)
        stmt = select(self.model).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_teacher(self, teacher_id: int) -> List[LessonSlot]:
        """Все слоты преподавателя."""
        stmt = select(self.model).where(self.model.teacher_id == teacher_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_for_period(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[LessonSlot]:
        """Слоты за период."""
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

    async def find_room_lesson_conflicts(
        self,
        room_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[LessonSlot]:
        """Слоты уроков, пересекающиеся с указанным интервалом для данной комнаты."""
        stmt = select(self.model).where(
            and_(
                self.model.room_id == room_id,
                self.model.start_time < end_time,
                self.model.end_time > start_time
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_slot_with_bookings(self, slot_id: int) -> Optional[LessonSlot]:
        """Слот с количеством записей (с подгруженными бронированиями)."""
        stmt = (
            select(self.model)
            .options(selectinload(self.model.lesson_bookings))
            .where(self.model.id == slot_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()