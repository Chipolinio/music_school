from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.repositories.BaseRepository import BaseRepository
from src.models.Notification import Notification

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    async def get_unread(self, user_id: int):
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_read == False
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_all_as_read(self, user_id: int):
        stmt = update(self.model).where(
            self.model.user_id == user_id,
            self.model.is_read == False
        ).values(is_read=True)
        await self.session.execute(stmt)
        await self.session.flush()