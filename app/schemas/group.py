from fastapi import Query
from fastapi_pagination import Params
from pydantic import BaseModel, ConfigDict, constr


class GroupBase(BaseModel):
    name: str


class GroupCreateRequest(GroupBase):
    pass


class GroupCreate(GroupBase):
    creator_id: int
    chat_id: int


class GroupUpdate(GroupBase):
    pass


class Group(GroupCreate):
    id: int  # noqa: A003

    model_config = ConfigDict(from_attributes=True)


class GroupUsersCreateRequest(BaseModel):
    group_id: int
    user_ids: list[int]


class GroupRequest(Params):
    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(10, ge=1, le=20, description='Page size')

    search_term: constr(min_length=3)


class GroupMembersRequest(Params):
    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(10, ge=1, le=20, description='Page size')
