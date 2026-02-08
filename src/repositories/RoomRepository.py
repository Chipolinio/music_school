from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .BaseRepository import BaseRepository
from src.models.Room  import Room

class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(Room, session)

    async def get_active_rooms(self):
        stmt = select(self.model).where(self.model.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()