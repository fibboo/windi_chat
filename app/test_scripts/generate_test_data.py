import asyncio
from uuid import uuid4

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.crud.chat import chat_user_crud
from app.crud.message import message_crud
from app.crud.user import user_crud
from app.db.postgres import session_maker
from app.models.user import User as UserModel
from app.schemas.chat import Chat, ChatUserCreate
from app.schemas.group import Group, GroupCreateRequest
from app.schemas.message import MessageCreate
from app.schemas.user import UserCreate
from app.services import chat_service, group_service

logger = get_logger(__name__)


async def create_test_data(db: AsyncSession) -> None:
    users_create_data: list[UserCreate] = []
    for i in range(100):
        hashed_password: str = bcrypt.hashpw('password'.encode(), bcrypt.gensalt(rounds=4)).decode()
        users_create_data.append(UserCreate(username=f'user{i}', password=hashed_password))
    users_db: list[UserModel] = await user_crud.create_batch(db=db, objs_in=users_create_data)
    logger.debug(f'Created {len(users_db)} users')

    messages_create_data: list[MessageCreate] = []
    chats_count: int = 0
    for user_db in users_db[:50]:
        for user_db_2 in users_db[50:]:
            chat: Chat = await chat_service.create_private_chat(db=db,
                                                                user_id=user_db.id,
                                                                current_user_id=user_db_2.id)
            chats_count += 1

            for i in range(10):
                text = f'test message {i} from {user_db.username} to {user_db_2.username}'
                messages_create_data.append(MessageCreate(id=uuid4(),
                                                          chat_id=chat.id,
                                                          text=text,
                                                          sender_id=user_db.id))

                text = f'test message {i} from {user_db_2.username} to {user_db.username}'
                messages_create_data.append(MessageCreate(id=uuid4(),
                                                          chat_id=chat.id,
                                                          text=text,
                                                          sender_id=user_db_2.id))
    logger.debug(f'Created {chats_count} private chats with {len(messages_create_data)} messages')

    chat_users_create: list[ChatUserCreate] = []
    group_count: int = 0
    for i in range(10):
        create_data: GroupCreateRequest = GroupCreateRequest(name=f'test group {i}')
        group: Group = await group_service.create_group(db=db, create_data=create_data, current_user_id=users_db[i].id)
        group_count += 1

        for user_db in users_db[i + 1:20]:
            chat_users_create.append(ChatUserCreate(chat_id=group.chat_id, user_id=user_db.id))

            for y in range(3):
                text = f'test message {y} from {user_db.username} to {group.name}'
                messages_create_data.append(MessageCreate(id=uuid4(),
                                                          chat_id=group.chat_id,
                                                          text=text,
                                                          sender_id=user_db.id))

    await chat_user_crud.create_batch(db=db, objs_in=chat_users_create)
    await message_crud.create_batch(db=db, objs_in=messages_create_data)
    logger.debug(f'Created {group_count} groups with chats and {len(messages_create_data)} messages')


async def main() -> None:
    try:
        async with session_maker.begin() as session:
            await create_test_data(db=session)

    finally:
        await session.commit()
        await session.close()


if __name__ == '__main__':
    asyncio.run(main())
    logger.debug('Create test data finished successfully')
