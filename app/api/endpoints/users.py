from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_db_transaction, get_user_id
from app.schemas.user import User, UserCreateRequest, UserRequest
from app.services import user_service

router = APIRouter()


@router.post('')
async def create_user(create_data: UserCreateRequest,
                      db: AsyncSession = Depends(get_db_transaction)) -> User:
    user: User = await user_service.create_user(db=db, create_data=create_data)
    return user


@router.get('')
async def get_users(request: UserRequest = Depends(),
                    current_user_id: int = Depends(get_user_id),
                    db: AsyncSession = Depends(get_db)) -> Page[User]:
    users: Page[User] = await user_service.get_users(db=db, request=request, current_user_id=current_user_id)
    return users


@router.get('/me')
async def get_current_user(current_user_id: int = Depends(get_user_id),
                           db: AsyncSession = Depends(get_db)) -> User:
    user: User = await user_service.get_user(db=db, user_id=current_user_id)
    return user


@router.get('/{user_id}')
async def get_user(user_id: int,
                   _: int = Depends(get_user_id),
                   db: AsyncSession = Depends(get_db)) -> User:
    user: User = await user_service.get_user(db=db, user_id=user_id)
    return user
