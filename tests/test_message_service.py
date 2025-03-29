from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi_pagination import Page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.forbidden_403 import UserNotChatMemberException
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.message import Message as MessageModel, MessageUserRead
from app.schemas.chat import Chat
from app.schemas.error_response import ErrorCodeType
from app.schemas.group import Group, GroupCreateRequest, GroupUsersCreateRequest
from app.schemas.message import Message, MessageCreateRequest, MessageRequest
from app.schemas.user import User, UserCreateRequest
from app.services import chat_service, group_service, message_service, user_service


@pytest.fixture
def mock_send_message():
    with patch('app.services.message_service.websocket_manager.send_message', autospec=True) as mock_send:
        yield mock_send


@pytest.mark.asyncio
async def test_send_message_ok(db: AsyncSession, db_transaction: AsyncSession, mock_send_message: AsyncMock):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    chat: Chat = await chat_service.create_private_chat(db=db, user_id=user1.id, current_user_id=user2.id)
    await db.commit()

    create_data: MessageCreateRequest = MessageCreateRequest(id=uuid4(), chat_id=chat.id, text='text')

    # Act
    message: Message = await message_service.send_message(db=db_transaction, create_data=create_data,
                                                          current_user_id=user1.id, device_id='1')
    await db_transaction.commit()

    # Assert
    assert message is not None
    assert message.id == create_data.id
    assert message.chat_id == chat.id
    assert message.text == create_data.text
    assert message.sender_id == user1.id
    assert message.send_at is not None
    assert message.read_at is None
    assert message.chat is not None

    assert mock_send_message.call_count == 1

    messages_db: list[MessageModel] = (await db.scalars(select(MessageModel))).all()
    assert len(messages_db) == 1

    message_users_read: list[MessageUserRead] = (await db.scalars(select(MessageUserRead))).all()
    assert len(message_users_read) == 1


@pytest.mark.asyncio
async def test_send_message_not_chat_member(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    chat: Chat = await chat_service.create_private_chat(db=db, user_id=user1.id, current_user_id=user2.id)
    await db.commit()

    create_data: MessageCreateRequest = MessageCreateRequest(id=uuid4(), chat_id=chat.id, text='text')
    wrong_user_id = 10

    # Act
    with pytest.raises(UserNotChatMemberException) as exc:
        await message_service.send_message(db=db_transaction, create_data=create_data, current_user_id=wrong_user_id,
                                           device_id='1')
        await db_transaction.commit()

    # Assert
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.message == 'User is not a chat member'
    assert exc.value.log_message == f'User `{wrong_user_id}` is not a chat `{chat.id}` member'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.USER_NOT_CHAT_MEMBER


@pytest.mark.asyncio
async def test_get_message_ok(db: AsyncSession, mock_send_message: AsyncMock):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    chat: Chat = await chat_service.create_private_chat(db=db, user_id=user1.id, current_user_id=user2.id)

    create_data: MessageCreateRequest = MessageCreateRequest(id=uuid4(), chat_id=chat.id, text='text')
    message_before: Message = await message_service.send_message(db=db, create_data=create_data,
                                                                 current_user_id=user1.id, device_id='1')
    await db.commit()

    # Act
    message: Message = await message_service.get_message(db=db, message_id=message_before.id)

    # Assert
    assert message is not None
    assert message.id == message_before.id
    assert message.chat_id == message_before.chat_id
    assert message.text == message_before.text
    assert message.sender_id == message_before.sender_id
    assert message.send_at is not None
    assert message.read_at is None
    assert message.chat is not None


@pytest.mark.asyncio
async def test_get_message_not_found(db: AsyncSession):
    # Arrange
    message_id: UUID = uuid4()

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await message_service.get_message(db=db, message_id=message_id)

    # Assert
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.message == 'Entity not found'
    search_params = {'id': message_id}
    assert exc.value.log_message == f'{MessageModel.__name__} not found by {search_params}'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND


@pytest.mark.asyncio
async def test_get_messages(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    chat: Chat = await chat_service.create_private_chat(db=db, user_id=user1.id, current_user_id=user2.id)

    for i in range(3):
        create_data: MessageCreateRequest = MessageCreateRequest(id=uuid4(), chat_id=chat.id, text=f'text{i}')
        await message_service.send_message(db=db, create_data=create_data,
                                           current_user_id=user1.id, device_id='1')
    await db.commit()

    request_p1: MessageRequest = MessageRequest(page=1, size=2)
    request_p2: MessageRequest = MessageRequest(page=2, size=2)

    # Act
    messages_p1: Page[Message] = await message_service.get_messages(db=db, chat_id=chat.id, request=request_p1)
    messages_p2: Page[Message] = await message_service.get_messages(db=db, chat_id=chat.id, request=request_p2)

    # Assert
    assert messages_p1.total == 3
    assert len(messages_p1.items) == 2
    assert messages_p1.items[0].text == 'text0'
    assert messages_p1.items[1].text == 'text1'

    assert messages_p2.total == 3
    assert len(messages_p2.items) == 1
    assert messages_p2.items[0].text == 'text2'


@pytest.mark.asyncio
async def test_read_message_private(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    chat: Chat = await chat_service.create_private_chat(db=db, user_id=user1.id, current_user_id=user2.id)

    create_data: MessageCreateRequest = MessageCreateRequest(id=uuid4(), chat_id=chat.id, text='text')
    message_before: Message = await message_service.send_message(db=db, create_data=create_data,
                                                                 current_user_id=user1.id, device_id='1')
    await db.commit()

    # Act
    message: Message = await message_service.read_message(db=db_transaction, message_id=message_before.id,
                                                          current_user_id=user2.id)
    await db_transaction.commit()

    # Assert
    assert message is not None
    assert message.id == message_before.id
    assert message.chat_id == message_before.chat_id
    assert message.text == message_before.text
    assert message.sender_id == message_before.sender_id
    assert message.send_at is not None
    assert message_before.read_at is None
    assert message.read_at is not None


@pytest.mark.asyncio
async def test_read_message_group(db: AsyncSession, db_transaction: AsyncSession):
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

    create_data: MessageCreateRequest = MessageCreateRequest(id=uuid4(), chat_id=group.chat_id, text='text')
    message_before: Message = await message_service.send_message(db=db, create_data=create_data,
                                                                 current_user_id=user.id, device_id='1')
    await db.commit()

    # Act
    for user_id in user_ids:
        message: Message = await message_service.read_message(db=db_transaction, message_id=message_before.id,
                                                              current_user_id=user_id)
    await db_transaction.commit()

    # Assert
    assert message is not None
    assert message.id == message_before.id
    assert message.chat_id == message_before.chat_id
    assert message.text == message_before.text
    assert message.sender_id == message_before.sender_id
    assert message.send_at is not None
    assert message_before.read_at is None
    assert message.read_at is not None
