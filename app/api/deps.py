from typing import Annotated

from fastapi.params import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket

from app.configs.logging_settings import get_logger
from app.crud.user import user_crud
from app.db.postgres import session_maker
from app.exceptions.unauthorized_401 import InvalidTokenException
from app.exceptions.unprocessable_422 import UnprocessableException
from app.schemas.jwt import TokenData
from app.services import jwt_service
from app.models.user import User as UserModel

logger = get_logger(__name__)


async def get_db() -> AsyncSession:
    try:
        async with session_maker() as session:
            yield session

    finally:
        await session.commit()
        await session.close()


async def get_db_transaction() -> AsyncSession:
    try:
        async with session_maker.begin() as session:
            yield session

    finally:
        await session.commit()
        await session.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


async def _verify_token(db: AsyncSession, token: str) -> TokenData:
    token_data: TokenData = jwt_service.verify_token(token=token)

    user_db: UserModel | None = await user_crud.get_or_none(db=db, id=token_data.user_id)
    if user_db is None:
        raise InvalidTokenException(log_message=f'User with id `{token_data.user_id}` not found', logger=logger)

    return token_data


async def get_user_id(token: Annotated[str, Depends(oauth2_scheme)],
                      db: AsyncSession = Depends(get_db)) -> int:
    token_data: TokenData = await _verify_token(db=db, token=token)
    return token_data.user_id


def get_device_id(device_id: str = Header(...)) -> str:
    return device_id


async def get_user_id_ws(websocket: WebSocket,
                         db: AsyncSession = Depends(get_db)) -> int:
    token: str | None = websocket.headers.get('Authorization')
    if token is None:
        raise InvalidTokenException(log_message='No token in header', logger=logger)

    if not token.startswith('Bearer '):
        raise InvalidTokenException('Not Bearer token', logger=logger)
    token: str = token.replace('Bearer ', '')

    token_data: TokenData = await _verify_token(db=db, token=token)
    return token_data.user_id


def get_device_id_ws(websocket: WebSocket) -> str:
    device_id: str | None = websocket.headers.get('device_id')
    if device_id is None:
        raise UnprocessableException(log_message='No device_id in headers', logger=logger)

    return device_id
