from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEV = 'dev'
    PROD = 'prod'
    LOCAL = 'local'


class Settings(BaseSettings):
    environment: EnvironmentType = EnvironmentType.LOCAL
    app_title: str = 'FastAPI Template API'


settings = Settings()


class DatabaseSettings(BaseSettings):
    database_url: str = 'postgresql+asyncpg://user:password@localhost:5432/example_db'

    def db_sync_url(self):
        return self.database_url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')


database_settings = DatabaseSettings()


class ExampleSettingsWithPrefix(BaseSettings):
    param1: int = 1
    param2: str = '2'

    model_config = SettingsConfigDict(env_prefix='example_')
