from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.db.postgres import session_maker

logger = get_logger(__name__)


async def get_db() -> AsyncSession:
    session = session_maker()
    try:
        yield session

    finally:
        await session.commit()
        await session.close()


async def get_db_transaction() -> AsyncSession:
    async with session_maker.begin() as session:
        try:
            yield session

        finally:
            await session.commit()
            await session.close()
