import pytest
from fastapi_pagination import Page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.user import User as UserModel
from app.schemas.error_response import ErrorCodeType
from app.schemas.user import User, UserCreateRequest, UserRequest
from app.services import user_service


@pytest.mark.asyncio
async def test_create_user_ok(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data = UserCreateRequest(username='test', password='password')

    # Act
    user: User = await user_service.create_user(db=db_transaction, create_data=create_data)
    await db_transaction.commit()

    # Assert
    assert user is not None
    assert user.id is not None
    assert user.username == create_data.username

    user_db: list[UserModel] = (await db.scalars(select(UserModel))).all()
    assert len(user_db) == 1


@pytest.mark.asyncio
async def test_create_user_double(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data = UserCreateRequest(username='test', password='password')
    await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    # Act
    with pytest.raises(IntegrityException) as exc:
        await user_service.create_user(db=db, create_data=create_data)

    # Assert
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.message == 'Entity integrity error'
    assert exc.value.log_message == (f'User integrity error: DETAIL:  '
                                     f'Key (username)=({create_data.username}) already exists.')
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INTEGRITY_ERROR


@pytest.mark.asyncio
async def test_get_user_ok(db: AsyncSession):
    # Arrange
    create_data = UserCreateRequest(username='test', password='password')
    user_before: User = await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    # Act
    user: User = await user_service.get_user(db=db, user_id=user_before.id)

    # Assert
    assert user is not None
    assert user.id == user_before.id
    assert user.username == user_before.username


@pytest.mark.asyncio
async def test_get_user_not_found(db: AsyncSession):
    # Arrange
    user_id: int = 1

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await user_service.get_user(db=db, user_id=user_id)

    # Assert
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.message == 'Entity not found'
    search_params = {'id': user_id}
    assert exc.value.log_message == f'{UserModel.__name__} not found by {search_params}'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND


@pytest.mark.asyncio
async def test_get_users(db: AsyncSession):
    # Arrange
    for i in range(3):
        create_data = UserCreateRequest(username=f'test{i}', password='password')
        await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    request_p1: UserRequest = UserRequest(page=1, size=2)
    request_p2: UserRequest = UserRequest(page=2, size=2)

    # Act
    users_p1: Page[User] = await user_service.get_users(db=db, request=request_p1)
    users_p2: Page[User] = await user_service.get_users(db=db, request=request_p2)

    # Assert
    assert users_p1.total == 3
    assert len(users_p1.items) == 2
    assert users_p1.items[0].username == 'test0'
    assert users_p1.items[1].username == 'test1'

    assert users_p2.total == 3
    assert len(users_p2.items) == 1
    assert users_p2.items[0].username == 'test2'
