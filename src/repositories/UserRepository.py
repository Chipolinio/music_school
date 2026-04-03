from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .BaseRepository import BaseRepository
from src.models.User import User
from src.models.User import UserRole


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(self.model).where(self.model.phone == phone)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Получает пользователя по ID."""
        return await self.session.get(self.model, user_id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None
    ) -> Sequence[User]:
        stmt = select(self.model)
        if role is not None:
            stmt = stmt.where(self.model.role == role)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_user(
        self,
        phone: str,
        full_name: str,
        hashed_password: str,
        role: str = "STUDENT",
        is_active: bool = True,
    ) -> User:
        """Создаёт пользователя."""
        user = self.model(
            phone=phone,
            full_name=full_name,
            hashed_password=hashed_password,
            role=UserRole(role),
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user