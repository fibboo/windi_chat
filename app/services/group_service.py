from fastapi_pagination import Page
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.crud.chat import chat_user_crud
from app.crud.group import group_crud
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.forbidden_403 import UserNotGroupOwner
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.chat import ChatUser as ChatUserModel
from app.models.group import Group as GroupModel
from app.schemas.chat import Chat, ChatCreate, ChatType, ChatUserCreate
from app.schemas.group import (Group, GroupCreate, GroupCreateRequest, GroupMembersRequest, GroupRequest,
                               GroupUsersCreateRequest)
from app.schemas.user import User, UserRequest
from app.services import chat_service, user_service

logger = get_logger(__name__)


async def create_group(db: AsyncSession, create_data: GroupCreateRequest, current_user_id: int) -> Group:
    create_chat_data: ChatCreate = ChatCreate(name=create_data.name, type=ChatType.GROUP)
    chat: Chat = await chat_service.create_chat(db=db, create_data=create_chat_data)

    create_group_data: GroupCreate = GroupCreate(**create_data.model_dump(),
                                                 creator_id=current_user_id,
                                                 chat_id=chat.id)
    try:
        group_db: GroupModel = await group_crud.create(db=db, obj_in=create_group_data)

    except IntegrityError as exc:
        raise IntegrityException(entity=GroupModel, exception=exc, logger=logger)

    chat_user_create: ChatUserCreate = ChatUserCreate(chat_id=chat.id, user_id=current_user_id)
    try:
        await chat_user_crud.create(db=db, obj_in=chat_user_create)

    except IntegrityError as exc:
        raise IntegrityException(entity=ChatUserModel, exception=exc, logger=logger)

    group: Group = Group.model_validate(group_db)
    return group


async def add_users_to_group(db: AsyncSession,
                             group_users_request: GroupUsersCreateRequest,
                             current_user_id: int) -> None:
    group_db: GroupModel = await group_crud.get_or_none(db=db, id=group_users_request.group_id)
    if group_db is None:
        raise EntityNotFound(entity=GroupModel, search_params={'id': group_users_request.group_id}, logger=logger)

    if current_user_id != group_db.creator_id:
        raise UserNotGroupOwner(user_id=current_user_id, group_id=group_db.id, logger=logger)

    await chat_service.create_chat_users(db=db, chat_id=group_db.chat_id, user_ids=group_users_request.user_ids)


async def get_groups(db: AsyncSession, request: GroupRequest) -> Page[Group]:
    groups_db: Page[GroupModel] = await group_crud.get_groups(db=db, request=request)
    groups: Page[Group] = Page[Group].model_validate(groups_db)
    return groups


async def get_group(db: AsyncSession, group_id: int) -> Group:
    group_db: GroupModel | None = await group_crud.get_or_none(db=db, id=group_id)
    if group_db is None:
        raise EntityNotFound(entity=GroupModel, search_params={'id': group_id}, logger=logger)

    group: Group = Group.model_validate(group_db)
    return group


async def get_group_members(db: AsyncSession, group_id: int, request: GroupMembersRequest) -> Page[User]:
    group_db: GroupModel | None = await group_crud.get_or_none(db=db, id=group_id)
    if group_db is None:
        raise EntityNotFound(entity=GroupModel, search_params={'id': group_id}, logger=logger)

    request: UserRequest = UserRequest(page=request.page, size=request.size, chat_id=group_db.chat_id)
    users: Page[User] = await user_service.get_users(db=db, request=request)
    return users
