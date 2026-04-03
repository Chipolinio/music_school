from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .BaseRepository import BaseRepository
from src.models.Room import Room


class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(Room, session)

    async def get_active_rooms(self):
        stmt = select(self.model).where(self.model.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_room(
        self,
        name: str,
        capacity: int,
        is_active: bool = True,
    ) -> Room:
        """Создаёт комнату."""
        room = self.model(
            name=name,
            capacity=capacity,
            is_active=is_active,
        )
        self.session.add(room)
        await self.session.flush()
        await self.session.refresh(room)
        return room