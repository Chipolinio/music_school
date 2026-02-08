from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.BaseRepository import BaseRepository
from src.models.RehearsalBooking import RehearsalBooking


class RehearsalRepository(BaseRepository[RehearsalBooking]):
    def __init__(self, session: AsyncSession):
        super().__init__(RehearsalBooking, session)
