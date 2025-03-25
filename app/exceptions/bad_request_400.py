import logging

from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.base import AppBaseException
from app.schemas.error_response import ErrorCodeType


class BadRequestException(AppBaseException):
    def __init__(self,
                 message: str,
                 log_message: str,
                 logger: logging.Logger,
                 log_level: LogLevelType,
                 error_code: ErrorCodeType | None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST,
                         message=message,
                         log_message=log_message,
                         logger=logger,
                         log_level=log_level,
                         error_code=error_code)
