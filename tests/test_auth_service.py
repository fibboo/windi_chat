from datetime import datetime, timedelta

import pytest
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.configs.logging_settings import LogLevelType
from app.configs.settings import jwt_settings
from app.exceptions.unauthorized_401 import InvalidLoginDataException, InvalidTokenException
from app.schemas.error_response import ErrorCodeType
from app.schemas.jwt import Tokens, TokenType
from app.schemas.user import User, UserCreateRequest
from app.services import auth_service, user_service


@pytest.mark.asyncio
async def test_login_ok(db: AsyncSession):
    # Arrange
    now = datetime.now()
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    form_data: OAuth2PasswordRequestForm = OAuth2PasswordRequestForm(username=create_data.username,
                                                                     password=create_data.password)

    # Act
    tokens: Tokens = await auth_service.login(db=db, form_data=form_data)

    # Assert
    assert tokens is not None
    assert tokens.token_type == 'Bearer'
    assert tokens.access_token is not None
    assert tokens.access_token_expired_at < now + timedelta(seconds=jwt_settings.access_token_expire_seconds + 2)
    assert tokens.access_token_expired_at > now + timedelta(seconds=jwt_settings.access_token_expire_seconds - 2)
    assert tokens.refresh_token is not None
    assert tokens.refresh_token_expired_at < now + timedelta(seconds=jwt_settings.refresh_token_expire_seconds + 2)
    assert tokens.refresh_token_expired_at > now + timedelta(seconds=jwt_settings.refresh_token_expire_seconds - 2)


@pytest.mark.asyncio
async def test_login_user_not_found(db: AsyncSession):
    # Arrange
    form_data: OAuth2PasswordRequestForm = OAuth2PasswordRequestForm(username='username', password='password')

    # Act
    with pytest.raises(InvalidLoginDataException) as exc:
        await auth_service.login(db=db, form_data=form_data)

    # Assert
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.message == 'Username or password is incorrect'
    assert exc.value.log_message == f'User with username `{form_data.username}` does not exist'
    assert exc.value.log_level == LogLevelType.DEBUG
    assert exc.value.error_code == ErrorCodeType.INVALID_LOGIN_DATA


@pytest.mark.asyncio
async def test_login_wrong_password(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    form_data: OAuth2PasswordRequestForm = OAuth2PasswordRequestForm(username=create_data.username,
                                                                     password='wrong_password')

    # Act
    with pytest.raises(InvalidLoginDataException) as exc:
        await auth_service.login(db=db, form_data=form_data)

    # Assert
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.message == 'Username or password is incorrect'
    assert exc.value.log_message == f'Incorrect password for user `{form_data.username}` with id `{user.id}`'
    assert exc.value.log_level == LogLevelType.DEBUG
    assert exc.value.error_code == ErrorCodeType.INVALID_LOGIN_DATA


@pytest.mark.asyncio
async def test_refresh_token_ok(db: AsyncSession):
    # Arrange
    now = datetime.now()
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    form_data: OAuth2PasswordRequestForm = OAuth2PasswordRequestForm(username=create_data.username,
                                                                     password=create_data.password)
    tokens_before: Tokens = await auth_service.login(db=db, form_data=form_data)

    # Act
    tokens: Tokens = await auth_service.refresh_token(db=db, token=tokens_before.refresh_token)

    # Assert
    assert tokens is not None
    assert tokens.token_type == 'Bearer'
    assert tokens.access_token is not None
    assert tokens.access_token_expired_at < now + timedelta(seconds=jwt_settings.access_token_expire_seconds + 2)
    assert tokens.access_token_expired_at > now + timedelta(seconds=jwt_settings.access_token_expire_seconds - 2)
    assert tokens.refresh_token is not None
    assert tokens.refresh_token_expired_at < now + timedelta(seconds=jwt_settings.refresh_token_expire_seconds + 2)
    assert tokens.refresh_token_expired_at > now + timedelta(seconds=jwt_settings.refresh_token_expire_seconds - 2)


@pytest.mark.asyncio
async def test_refresh_token_invalid_token_type(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    form_data: OAuth2PasswordRequestForm = OAuth2PasswordRequestForm(username=create_data.username,
                                                                     password=create_data.password)
    tokens_before: Tokens = await auth_service.login(db=db, form_data=form_data)

    # Act
    with pytest.raises(InvalidTokenException) as exc:
        await auth_service.refresh_token(db=db, token=tokens_before.access_token)

    # Assert
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.message == 'Invalid token'
    assert exc.value.log_message == f'Invalid token type: {TokenType.ACCESS}'
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INVALID_TOKEN


@pytest.mark.asyncio
async def test_refresh_token_no_user(db: AsyncSession):
    # Arrange
    token: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjI2MDcxMzEwNTcuMzI3Nzc3fQ.JWXN9DOPC3ekVM1_pT0eK0zXyBFup__BccXp8eBYUgk'
    user_id: int = 1

    # Act
    with pytest.raises(InvalidTokenException) as exc:
        await auth_service.refresh_token(db=db, token=token)

    # Assert
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.message == 'Invalid token'
    assert exc.value.log_message == f'User with id `{user_id}` not found'
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INVALID_TOKEN
