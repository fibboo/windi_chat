import bcrypt
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.crud.user import user_crud
from app.exceptions.unauthorized_401 import InvalidLoginDataException, InvalidTokenException
from app.models.user import User as UserModel
from app.schemas.jwt import TokenData, TokenDataCreate, Tokens, TokenType
from app.services import jwt_service

logger = get_logger(__name__)


async def login(db: AsyncSession, form_data: OAuth2PasswordRequestForm) -> Tokens:
    user_db: UserModel | None = await user_crud.get_or_none(db=db, username=form_data.username)
    if user_db is None:
        raise InvalidLoginDataException(username=form_data.username, logger=logger)

    if not bcrypt.checkpw(form_data.password.encode(), user_db.password.encode()):
        raise InvalidLoginDataException(username=form_data.username, user_id=user_db.id, logger=logger)

    tokens: Tokens = jwt_service.generate_auth_tokens(token_data=TokenDataCreate(sub=str(user_db.id)))
    return tokens


async def refresh_token(db: AsyncSession, token: str) -> Tokens:
    token_data: TokenData = jwt_service.verify_token(token=token)
    if token_data.type != TokenType.REFRESH:
        raise InvalidTokenException(log_message=f'Invalid token type: {token_data.type}', logger=logger)

    user_db: UserModel | None = await user_crud.get_or_none(db=db, id=token_data.user_id)
    if user_db is None:
        raise InvalidTokenException(log_message=f'User with id `{token_data.user_id}` not found', logger=logger)

    tokens: Tokens = jwt_service.generate_auth_tokens(token_data=TokenDataCreate(sub=str(user_db.id)))
    return tokens
