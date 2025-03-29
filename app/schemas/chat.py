from enum import Enum

from fastapi import Query
from fastapi_pagination import Params
from pydantic import BaseModel, ConfigDict, constr


class ChatType(str, Enum):
    PRIVATE = 'PRIVATE'
    GROUP = 'GROUP'


class ChatBase(BaseModel):
    name: constr(min_length=3, max_length=256)
    type: ChatType  # noqa: A003


class ChatCreate(ChatBase):
    pass


class ChatUpdate(BaseModel):
    name: constr(min_length=3, max_length=256)


class Chat(ChatBase):
    id: int  # noqa: A003

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(Params):
    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(10, ge=1, le=20, description='Page size')

    search_term: constr(min_length=3)


class ChatUserBase(BaseModel):
    chat_id: int
    user_id: int


class ChatUserCreate(ChatUserBase):
    pass


class ChatUserUpdate(BaseModel):
    pass


class ChatUser(ChatUserBase):
    model_config = ConfigDict(from_attributes=True)
