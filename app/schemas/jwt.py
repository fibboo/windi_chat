from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TokenType(str, Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'


class TokenDataCreate(BaseModel):
    sub: str
    type: TokenType | None = None  # noqa: A003
    exp: float | None = None


class TokenData(BaseModel):
    user_id: int
    type: TokenType  # noqa: A003
    expired_at: datetime


class Tokens(BaseModel):
    token_type: str = 'Bearer'
    access_token: str
    access_token_expired_at: datetime
    refresh_token: str
    refresh_token_expired_at: datetime
