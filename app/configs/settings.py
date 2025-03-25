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


class JWTSettings(BaseSettings):
    algorithm: str = 'HS256'
    secret_key: str = 'secretkey'
    access_token_expire_seconds: int = 60 * 5  # 5 minutes
    refresh_token_expire_seconds: int = 60 * 60 * 24 * 30  # 30 days

    model_config = SettingsConfigDict(env_prefix='jwt_')


jwt_settings = JWTSettings()
