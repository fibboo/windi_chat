import pytest
from fastapi_pagination import Page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.forbidden_403 import UserNotGroupOwner
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.chat import Chat as ChatModel, ChatUser as ChatUserModel
from app.models.group import Group as GroupModel
from app.schemas.error_response import ErrorCodeType
from app.schemas.group import Group, GroupCreateRequest, GroupMembersRequest, GroupRequest, GroupUsersCreateRequest
from app.schemas.user import User, UserCreateRequest
from app.services import group_service, user_service


@pytest.mark.asyncio
async def test_create_group_ok(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    create_data: GroupCreateRequest = GroupCreateRequest(name='test')

    # Act
    group: Group = await group_service.create_group(db=db_transaction, create_data=create_data, current_user_id=user.id)
    await db_transaction.commit()

    # Assert
    assert group is not None
    assert group.id is not None
    assert group.name == create_data.name
    assert group.creator_id == user.id
    assert group.chat_id is not None

    groups_db: list[GroupModel] = (await db.scalars(select(GroupModel))).all()
    assert len(groups_db) == 1

    chats_db: list[ChatModel] = (await db.scalars(select(ChatModel))).all()
    assert len(chats_db) == 1
    assert chats_db[0].id == group.chat_id

    chat_users_db: list[ChatUserModel] = (await db.scalars(select(ChatUserModel))).all()
    assert len(chat_users_db) == 1
    assert chat_users_db[0].chat_id == group.chat_id
    assert chat_users_db[0].user_id == user.id


@pytest.mark.asyncio
async def test_create_group_double(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)

    create_data: GroupCreateRequest = GroupCreateRequest(name='test')
    await group_service.create_group(db=db, create_data=create_data, current_user_id=user.id)
    await db.commit()

    # Act
    with pytest.raises(IntegrityException) as exc:
        await group_service.create_group(db=db_transaction, create_data=create_data, current_user_id=user.id)

    # Assert
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.message == 'Entity integrity error'
    assert exc.value.log_message == (f'Chat integrity error: DETAIL:  '
                                     f'Key (name)=({create_data.name}) already exists.')
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INTEGRITY_ERROR

    groups_db: list[GroupModel] = (await db.scalars(select(GroupModel))).all()
    assert len(groups_db) == 1

    chats_db: list[ChatModel] = (await db.scalars(select(ChatModel))).all()
    assert len(chats_db) == 1


@pytest.mark.asyncio
async def test_add_users_to_group(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)

    create_data: GroupCreateRequest = GroupCreateRequest(name='test')
    group: Group = await group_service.create_group(db=db, create_data=create_data, current_user_id=user.id)

    user_ids: list[int] = []
    for i in range(10):
        create_data: UserCreateRequest = UserCreateRequest(username=f'user{i}', password='password')
        member_user: User = await user_service.create_user(db=db, create_data=create_data)
        user_ids.append(member_user.id)
    await db.commit()

    group_users_request: GroupUsersCreateRequest = GroupUsersCreateRequest(group_id=group.id, user_ids=user_ids)

    # Act
    await group_service.add_users_to_group(db=db_transaction,
                                           group_users_request=group_users_request,
                                           current_user_id=user.id)
    await db_transaction.commit()

    # Assert
    chat_users_db: list[ChatUserModel] = (await db.scalars(select(ChatUserModel))).all()
    assert len(chat_users_db) == 11
    for chat_user in chat_users_db:
        assert chat_user.chat_id == group.chat_id
        assert chat_user.user_id in user_ids or chat_user.user_id == user.id


@pytest.mark.asyncio
async def test_add_users_to_group_no_group(db: AsyncSession):
    # Arrange
    group_users_request: GroupUsersCreateRequest = GroupUsersCreateRequest(group_id=1, user_ids=[1])

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await group_service.add_users_to_group(db=db,
                                               group_users_request=group_users_request,
                                               current_user_id=1)
    # Assert
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.message == 'Entity not found'
    search_params = {'id': group_users_request.group_id}
    assert exc.value.log_message == f'{GroupModel.__name__} not found by {search_params}'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND


@pytest.mark.asyncio
async def test_add_users_to_group_not_creator(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)

    create_data: GroupCreateRequest = GroupCreateRequest(name='test')
    group: Group = await group_service.create_group(db=db, create_data=create_data, current_user_id=user.id)
    await db.commit()

    group_users_request: GroupUsersCreateRequest = GroupUsersCreateRequest(group_id=group.id, user_ids=[1])

    wrong_user_id: int = 2

    # Act
    with pytest.raises(UserNotGroupOwner) as exc:
        await group_service.add_users_to_group(db=db,
                                               group_users_request=group_users_request,
                                               current_user_id=wrong_user_id)
    # Assert
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.message == 'User is not an owner of the group'
    assert exc.value.log_message == f'User `{wrong_user_id}` is not an owner of the group `{group.id}`'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.USER_IS_NOT_GROUP_OWNER


@pytest.mark.asyncio
async def test_get_groups(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)

    for i in range(3):
        create_data: GroupCreateRequest = GroupCreateRequest(name=f'test{i}')
        await group_service.create_group(db=db, create_data=create_data, current_user_id=user.id)
    await db.commit()

    request_p1: GroupRequest = GroupRequest(page=1, size=2, search_term='test')
    request_p2: GroupRequest = GroupRequest(page=2, size=2, search_term='test')
    request_search: GroupRequest = GroupRequest(page=1, size=2, search_term='test1')

    # Act
    groups_p1: Page[Group] = await group_service.get_groups(db=db, request=request_p1)
    groups_p2: Page[Group] = await group_service.get_groups(db=db, request=request_p2)
    groups_search: Page[Group] = await group_service.get_groups(db=db, request=request_search)

    # Assert
    assert groups_p1.total == 3
    assert len(groups_p1.items) == 2
    assert groups_p1.items[0].name == 'test0'
    assert groups_p1.items[1].name == 'test1'

    assert groups_p2.total == 3
    assert len(groups_p2.items) == 1
    assert groups_p2.items[0].name == 'test2'

    assert groups_search.total == 1
    assert len(groups_search.items) == 1
    assert groups_search.items[0].name == 'test1'


@pytest.mark.asyncio
async def test_get_group_ok(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)

    create_data: GroupCreateRequest = GroupCreateRequest(name='test')
    group_before: Group = await group_service.create_group(db=db, create_data=create_data, current_user_id=user.id)
    await db.commit()

    # Act
    group: Group = await group_service.get_group(db=db, group_id=group_before.id)

    # Assert
    assert group is not None
    assert group.id == group_before.id
    assert group.name == group_before.name
    assert group.creator_id == group_before.creator_id
    assert group.chat_id == group_before.chat_id


@pytest.mark.asyncio
async def test_get_group_not_found(db: AsyncSession):
    # Arrange
    group_id: int = 1

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await group_service.get_group(db=db, group_id=group_id)

    # Assert
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.message == 'Entity not found'
    search_params = {'id': group_id}
    assert exc.value.log_message == f'{GroupModel.__name__} not found by {search_params}'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND


@pytest.mark.asyncio
async def test_get_group_members_ok(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user', password='password')
    user: User = await user_service.create_user(db=db, create_data=create_data)

    create_data: GroupCreateRequest = GroupCreateRequest(name='test')
    group: Group = await group_service.create_group(db=db, create_data=create_data, current_user_id=user.id)

    user_ids: list[int] = []
    for i in range(2):
        create_data: UserCreateRequest = UserCreateRequest(username=f'user{i}', password='password')
        member_user: User = await user_service.create_user(db=db, create_data=create_data)
        user_ids.append(member_user.id)

    group_users_request: GroupUsersCreateRequest = GroupUsersCreateRequest(group_id=group.id, user_ids=user_ids)
    await group_service.add_users_to_group(db=db,
                                           group_users_request=group_users_request,
                                           current_user_id=user.id)
    await db.commit()

    request_p1: GroupMembersRequest = GroupMembersRequest(page=1, size=2)
    request_p2: GroupMembersRequest = GroupMembersRequest(page=2, size=2)

    # Arrange
    members_p1: Page[User] = await group_service.get_group_members(db=db, group_id=group.id, request=request_p1)
    members_p2: Page[User] = await group_service.get_group_members(db=db, group_id=group.id, request=request_p2)

    # Assert
    assert members_p1.total == 3
    assert len(members_p1.items) == 2
    assert members_p1.items[0].username == 'user'
    assert members_p1.items[1].username == 'user0'

    assert members_p2.total == 3
    assert len(members_p2.items) == 1
    assert members_p2.items[0].username == 'user1'


@pytest.mark.asyncio
async def test_get_group_members_group_not_found(db: AsyncSession):
    # Arrange
    group_id: int = 1

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await group_service.get_group_members(db=db, group_id=group_id, request=GroupMembersRequest())

    # Assert
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.message == 'Entity not found'
    search_params = {'id': group_id}
    assert exc.value.log_message == f'{GroupModel.__name__} not found by {search_params}'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND
