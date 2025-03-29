from fastapi import Query
from fastapi_pagination import Params
from pydantic import BaseModel, ConfigDict, constr


class UserBase(BaseModel):
    username: constr(max_length=256)


class UserCreateRequest(UserBase):
    password: constr(min_length=6, max_length=16)


class UserCreate(UserBase):
    password: constr(min_length=60, max_length=60)


class UserUpdate(UserBase):
    password: constr(min_length=6, max_length=16)


class User(UserBase):
    id: int  # noqa: A003

    model_config = ConfigDict(from_attributes=True)


class UserRequest(Params):
    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(10, ge=1, le=20, description='Page size')

    chat_id: int | None = None
    search_term: constr(min_length=3) | None = None
