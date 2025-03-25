import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.unauthorized_401 import InvalidTokenException, TokenExpiredException
from app.schemas.error_response import ErrorCodeType
from app.services import jwt_service


def test_verify_token_expired(db: AsyncSession):
    # Arrange
    token: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc0MzIxMDUxOS4yMDUxMDh9.8LNFDmKIFKGG6ogmn6YAVbdEcDMLJyJItll9x80B8uk'

    # Act
    with pytest.raises(TokenExpiredException) as exc:
        jwt_service.verify_token(token=token)

    # Assert
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.message == 'Token is expired'
    assert exc.value.log_message == 'ExpiredSignatureError: Signature has expired.'
    assert exc.value.log_level == LogLevelType.DEBUG
    assert exc.value.error_code == ErrorCodeType.TOKEN_EXPIRED


def test_verify_token_invalid(db: AsyncSession):
    # Arrange
    token: str = 'eyJhbGciOiJIUz1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc0MzIxMDUxOS4yMDUxMDh9.8LNFDmKIFKGG6ogmn6YAVbdEcDMLJyJItll9x80B8uk'

    # Act
    with pytest.raises(InvalidTokenException) as exc:
        jwt_service.verify_token(token=token)

    # Assert
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.message == 'Invalid token'
    assert exc.value.log_message == ("JWTError: Invalid header string: 'utf-8' codec can't decode "
                                     'byte 0x88 in position 12: invalid start byte')
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INVALID_TOKEN
