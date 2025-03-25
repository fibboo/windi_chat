import logging

from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.base import AppBaseException
from app.schemas.error_response import ErrorCodeType


class UnauthorizedException(AppBaseException):
    def __init__(self,
                 message: str,
                 log_message: str,
                 logger: logging.Logger,
                 log_level: LogLevelType,
                 error_code: ErrorCodeType | None = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED,
                         message=message,
                         log_message=log_message,
                         logger=logger,
                         log_level=log_level,
                         error_code=error_code)


class InvalidLoginDataException(UnauthorizedException):
    def __init__(self, username: str, logger: logging.Logger, user_id: int | None = None):
        if user_id is not None:
            log_message: str = f'Incorrect password for user `{username}` with id `{user_id}`'
        else:
            log_message: str = f'User with username `{username}` does not exist'

        super().__init__(message='Username or password is incorrect',
                         log_message=log_message,
                         logger=logger,
                         log_level=LogLevelType.DEBUG,
                         error_code=ErrorCodeType.INVALID_LOGIN_DATA)


class InvalidTokenException(UnauthorizedException):
    def __init__(self, log_message: str, logger: logging.Logger):
        super().__init__(message='Invalid token',
                         log_message=log_message,
                         logger=logger,
                         log_level=LogLevelType.WARNING,
                         error_code=ErrorCodeType.INVALID_TOKEN)


class TokenExpiredException(UnauthorizedException):
    def __init__(self, log_message: str, logger: logging.Logger):
        super().__init__(message='Token is expired',
                         log_message=log_message,
                         logger=logger,
                         log_level=LogLevelType.DEBUG,
                         error_code=ErrorCodeType.TOKEN_EXPIRED)
