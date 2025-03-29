import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.configs.logging_settings import LogLevelType
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.chat import Chat as ChatModel, ChatUser as ChatUserModel
from app.schemas.chat import Chat, ChatCreate, ChatType
from app.schemas.error_response import ErrorCodeType
from app.schemas.user import User, UserCreateRequest
from app.services import chat_service, user_service


@pytest.mark.asyncio
async def test_create_private_chat_ok(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)
    await db.commit()

    # Act
    chat: Chat = await chat_service.create_private_chat(db=db_transaction, user_id=user1.id, current_user_id=user2.id)
    await db_transaction.commit()

    # Assert
    assert chat is not None
    assert chat.id is not None
    assert chat.name == f'Private-[{user1.id}, {user2.id}]'
    assert chat.type == ChatType.PRIVATE

    chats_db: list[ChatModel] = (await db.scalars(select(ChatModel))).all()
    assert len(chats_db) == 1

    chat_users_db: list[ChatUserModel] = (await db.scalars(select(ChatUserModel))).all()
    assert len(chat_users_db) == 2


@pytest.mark.asyncio
async def test_create_chat_double(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: ChatCreate = ChatCreate(name='test', type=ChatType.PRIVATE)
    await chat_service.create_chat(db=db, create_data=create_data)
    await db.commit()

    # Act
    with pytest.raises(IntegrityException) as exc:
        await chat_service.create_chat(db=db_transaction, create_data=create_data)
        await db_transaction.commit()

    # Assert
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.message == 'Entity integrity error'
    assert exc.value.log_message == f'Chat integrity error: DETAIL:  Key (name)=({create_data.name}) already exists.'
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INTEGRITY_ERROR

    chats_db: list[ChatModel] = (await db.scalars(select(ChatModel))).all()
    assert len(chats_db) == 1


@pytest.mark.asyncio
async def test_create_chat_users_double(db: AsyncSession, db_transaction: AsyncSession):
    # Arrange
    create_data: ChatCreate = ChatCreate(name='test', type=ChatType.PRIVATE)
    chat: Chat = await chat_service.create_chat(db=db, create_data=create_data)

    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    await chat_service.create_chat_users(db=db, chat_id=chat.id, user_ids=[user1.id, user2.id])
    await db.commit()

    # Act
    with pytest.raises(IntegrityException) as exc:
        await chat_service.create_chat_users(db=db_transaction, chat_id=chat.id, user_ids=[user1.id, user2.id])
        await db_transaction.commit()

    # Assert
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.message == 'Entity integrity error'
    assert exc.value.log_message == (f'ChatUser integrity error: DETAIL:  '
                                     f'Key (chat_id, user_id)=({chat.id}, {user1.id}) already exists.')
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INTEGRITY_ERROR

    chats_db: list[ChatUserModel] = (await db.scalars(select(ChatUserModel))).all()
    assert len(chats_db) == 2


@pytest.mark.asyncio
async def test_get_chat_ok(db: AsyncSession):
    # Arrange
    create_data: UserCreateRequest = UserCreateRequest(username='user1', password='password')
    user1: User = await user_service.create_user(db=db, create_data=create_data)
    create_data: UserCreateRequest = UserCreateRequest(username='user2', password='password')
    user2: User = await user_service.create_user(db=db, create_data=create_data)

    chat_before: Chat = await chat_service.create_private_chat(db=db, user_id=user1.id, current_user_id=user2.id)
    await db.commit()

    # Act
    chat: Chat = await chat_service.get_chat(db=db, chat_id=chat_before.id, current_user_id=user1.id)

    # Assert
    assert chat is not None
    assert chat.id == chat_before.id
    assert chat.name == chat_before.name
    assert chat.type == chat_before.type


@pytest.mark.asyncio
async def test_get_chat_not_found(db: AsyncSession):
    # Arrange
    chat_id: int = 1

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await chat_service.get_chat(db=db, chat_id=chat_id, current_user_id=1)

    # Assert
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.message == 'Entity not found'
    search_params = {'id': chat_id}
    assert exc.value.log_message == f'{ChatModel.__name__} not found by {search_params}'
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND
