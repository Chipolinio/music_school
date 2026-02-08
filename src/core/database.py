from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from settings import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
)

session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session():
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()