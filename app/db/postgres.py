from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.configs.settings import database_settings, EnvironmentType, settings

engine = create_async_engine(database_settings.database_url,
                             pool_pre_ping=True,
                             pool_size=2,
                             max_overflow=30 if settings.environment == EnvironmentType.PROD else 10,
                             # echo=True  # When True, enable log output for every query
                             )

session_maker = async_sessionmaker(engine, autocommit=False, autoflush=False, expire_on_commit=False)
