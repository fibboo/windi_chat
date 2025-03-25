from enum import Enum

from pydantic import BaseModel
from starlette import status


class ErrorCodeType(str, Enum):
    ENTITY_NOT_FOUND = 'ENTITY_NOT_FOUND'
    INTEGRITY_ERROR = 'INTEGRITY_ERROR'

    NOT_IMPLEMENTED = 'NOT_IMPLEMENTED'

    USER_NOT_CHAT_MEMBER = 'USER_NOT_CHAT_MEMBER'
    USER_IS_NOT_GROUP_OWNER = 'USER_IS_NOT_GROUP_OWNER'

    INVALID_LOGIN_DATA = 'INVALID_LOGIN_DATA'
    INVALID_TOKEN = 'INVALID_TOKEN'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'


class ErrorResponse(BaseModel):
    message: str
    error_code: ErrorCodeType | None = None


responses = {
    status.HTTP_418_IM_A_TEAPOT: {
        'description': 'Custom errors with possible codes: 400, 401, 403, 404, 409, 501',
        'model': ErrorResponse
    }
}
