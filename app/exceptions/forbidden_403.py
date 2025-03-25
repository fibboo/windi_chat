import logging

from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.base import AppBaseException
from app.schemas.error_response import ErrorCodeType


class ForbiddenException(AppBaseException):
    def __init__(self,
                 message: str,
                 log_message: str,
                 logger: logging.Logger,
                 log_level: LogLevelType,
                 error_code: ErrorCodeType | None = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN,
                         message=message,
                         log_message=log_message,
                         logger=logger,
                         log_level=log_level,
                         error_code=error_code)


class UserNotChatMemberException(ForbiddenException):
    def __init__(self, user_id: int, chat_id: int, logger: logging.Logger):
        super().__init__(message='User is not a chat member',
                         log_message=f'User `{user_id}` is not a chat `{chat_id}` member',
                         logger=logger,
                         log_level=LogLevelType.ERROR,
                         error_code=ErrorCodeType.USER_NOT_CHAT_MEMBER)


class UserNotGroupOwner(ForbiddenException):
    def __init__(self, user_id: int, group_id: int, logger: logging.Logger):
        super().__init__(message='User is not an owner of the group',
                         log_message=f'User `{user_id}` is not an owner of the group `{group_id}`',
                         logger=logger,
                         log_level=LogLevelType.ERROR,
                         error_code=ErrorCodeType.USER_IS_NOT_GROUP_OWNER)
