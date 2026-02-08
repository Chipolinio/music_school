from typing import TypeVar, Type, Generic, Sequence, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, model_instance: T) -> T:
        self.session.add(model_instance)
        await self.session.flush()
        await self.session.refresh(model_instance)
        return model_instance

    async def get_by_id(self, obj_id: int) -> Optional[T]:
        return await self.session.get(self.model, obj_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, model_instance: T) -> T:
        self.session.add(model_instance)
        await self.session.flush()
        await self.session.refresh(model_instance)
        return model_instance

    async def delete(self, model_instance: T) -> None:
        await self.session.delete(model_instance)
        await self.session.flush()