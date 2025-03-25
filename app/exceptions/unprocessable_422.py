import logging

from app.configs.logging_settings import LogLevelType
from app.exceptions.base import AppBaseException
from app.schemas.error_response import ErrorCodeType, ErrorStatusType


class UnprocessableException(AppBaseException):
    def __init__(self,
                 log_message: str,
                 logger: logging.Logger,
                 log_level: LogLevelType = LogLevelType.WARNING,
                 title: str = 'Unprocessable entity',
                 error_code: ErrorCodeType | None = None):
        super().__init__(status_code=ErrorStatusType.HTTP_422_UNPROCESSABLE_ENTITY,
                         title=title,
                         log_message=log_message,
                         logger=logger,
                         log_level=log_level,
                         error_code=error_code)
