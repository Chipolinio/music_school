from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .BaseRepository import BaseRepository
from src.models.User  import User

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_tg_id(self, telegram_id: int) -> User | None:
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(self.model).where(self.model.phone == phone)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()