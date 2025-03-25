from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_transaction, get_user_id
from app.schemas.group import Group, GroupCreateRequest, GroupMembersRequest, GroupRequest, GroupUsersCreateRequest
from app.schemas.user import User
from app.services import group_service

router = APIRouter()


@router.post('')
async def create_group(create_data: GroupCreateRequest,
                       current_user_id: int = Depends(get_user_id),
                       db: AsyncSession = Depends(get_db_transaction)) -> Group:
    group: Group = await group_service.create_group(db=db, create_data=create_data, current_user_id=current_user_id)
    return group


@router.post('/add-users')
async def add_users_to_group(group_users_request: GroupUsersCreateRequest,
                             current_user_id: int = Depends(get_user_id),
                             db: AsyncSession = Depends(get_db_transaction)) -> None:
    await group_service.add_users_to_group(db=db,
                                           group_users_request=group_users_request,
                                           current_user_id=current_user_id)


@router.get('')
async def get_groups(request: GroupRequest = Depends(),
                     _: int = Depends(get_user_id),
                     db: AsyncSession = Depends(get_db_transaction)) -> Page[Group]:
    groups: Page[Group] = await group_service.get_groups(db=db, request=request)
    return groups


@router.get('/{group_id}')
async def get_group(group_id: int,
                    _: int = Depends(get_user_id),
                    db: AsyncSession = Depends(get_db_transaction)) -> Group:
    group: Group = await group_service.get_group(db=db, group_id=group_id)
    return group


@router.get('/{group_id}/members')
async def get_group_members(group_id: int,
                            request: GroupMembersRequest = Depends(),
                            _: int = Depends(get_user_id),
                            db: AsyncSession = Depends(get_db_transaction)) -> Page[User]:
    users: Page[User] = await group_service.get_group_members(db=db, group_id=group_id, request=request)
    return users
