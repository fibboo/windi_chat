from datetime import datetime
from uuid import UUID

from fastapi import Query
from fastapi_pagination import Params
from pydantic import BaseModel, ConfigDict, constr, model_validator

from app.schemas.chat import Chat


class MessageCreateRequest(BaseModel):
    id: UUID  # noqa: A003
    chat_id: int
    text: constr(max_length=4096)


class MessageCreate(MessageCreateRequest):
    sender_id: int


class MessageUpdate(BaseModel):
    text: constr(max_length=4096) | None = None
    read_at: datetime | None = None

    @model_validator(mode='after')
    def at_least_one_field_is_not_none(self):
        if len(self.model_fields_set) == 0:
            raise ValueError('At least one field is required')
        return self


class Message(MessageCreate):
    send_at: datetime
    read_at: datetime | None = None

    chat: Chat

    model_config = ConfigDict(from_attributes=True)


class MessageRequest(Params):
    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(10, ge=1, le=20, description='Page size')

    sender_id: int | None = None
    search_term: constr(min_length=3) | None = None


class MessageRead(BaseModel):
    message_id: UUID


class MessageUserReadCreate(BaseModel):
    message_id: UUID
    user_id: int


class MessageUserReadUpdate(BaseModel):
    pass
