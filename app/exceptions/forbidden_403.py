import logging

from app.configs.logging_settings import LogLevelType
from app.exceptions.base import AppBaseException
from app.schemas.error_response import ErrorCodeType, ErrorStatusType


class ForbiddenException(AppBaseException):
    def __init__(self,
                 title: str,
                 log_message: str,
                 logger: logging.Logger,
                 log_level: LogLevelType,
                 error_code: ErrorCodeType | None = None):
        super().__init__(status_code=ErrorStatusType.HTTP_403_FORBIDDEN,
                         title=title,
                         log_message=log_message,
                         logger=logger,
                         log_level=log_level,
                         error_code=error_code)
