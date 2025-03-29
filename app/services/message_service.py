from datetime import datetime
from uuid import UUID

from fastapi_pagination import Page
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.crud.chat import chat_user_crud
from app.crud.message import message_crud, message_user_read_crud
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.not_fount_404 import EntityNotFound
from app.exceptions.not_implemented_501 import NotImplementedException
from app.models.message import Message as MessageModel
from app.schemas.chat import Chat, ChatType
from app.schemas.message import Message, MessageCreate, MessageCreateRequest, MessageRequest, MessageUserReadCreate
from app.services import chat_service
from app.services.websocket_manager import websocket_manager

logger = get_logger(__name__)


async def send_message(db: AsyncSession,
                       create_data: MessageCreateRequest,
                       current_user_id: int,
                       device_id: str) -> Message:
    chat: Chat = await chat_service.get_chat(db=db, chat_id=create_data.chat_id, current_user_id=current_user_id)
    chat_user_ids: list[int] = await chat_user_crud.get_chat_user_ids(db=db, chat_id=chat.id)
    message_create: MessageCreate = MessageCreate(**create_data.model_dump(), sender_id=current_user_id)
    try:
        message_db: MessageModel = await message_crud.create(db=db, obj_in=message_create)

    except IntegrityError as exc:
        raise IntegrityException(entity=MessageModel, exception=exc, logger=logger)

    create_data: MessageUserReadCreate = MessageUserReadCreate(message_id=message_db.id, user_id=current_user_id)
    await message_user_read_crud.create(db=db, obj_in=create_data)

    message: Message = Message.model_validate(message_db)
    await websocket_manager.send_message(message=message,
                                         chat_id=chat.id,
                                         chat_user_ids=set(chat_user_ids),
                                         device_id=device_id)
    return message


async def get_message(db: AsyncSession, message_id: UUID) -> Message:
    message_db: MessageModel | None = await message_crud.get_or_none(db=db, id=message_id)
    if message_db is None:
        raise EntityNotFound(entity=MessageModel, search_params={'id': message_id}, logger=logger)

    message: Message = Message.model_validate(message_db)
    return message


async def get_messages(db: AsyncSession, chat_id: int, request: MessageRequest) -> Page[Message]:
    messages_db: Page[MessageModel] = await message_crud.get_messages(db=db, chat_id=chat_id, request=request)
    messages: Page[Message] = Page[Message].model_validate(messages_db)
    return messages


async def read_message(db: AsyncSession, message_id: UUID, current_user_id: int) -> Message:
    message: Message = await get_message(db=db, message_id=message_id)
    chat_user_ids: list[int] = await chat_user_crud.get_chat_user_ids(db=db, chat_id=message.chat.id)
    if current_user_id not in chat_user_ids:
        return message

    match message.chat.type:
        case ChatType.PRIVATE:
            if message.sender_id != current_user_id:
                message_db: MessageModel = await message_crud.update(db=db,
                                                                     id=message_id,
                                                                     obj_in={'read_at': datetime.now()})
                message: Message = Message.model_validate(message_db)

        case ChatType.GROUP:
            user_ids_read_message: list[int] = await message_user_read_crud.get_user_ids_read_message(db=db,
                                                                                                      message_id=message_id)
            if current_user_id not in user_ids_read_message:
                create_data: MessageUserReadCreate = MessageUserReadCreate(message_id=message_id,
                                                                           user_id=current_user_id)
                await message_user_read_crud.create(db=db, obj_in=create_data)
                user_ids_read_message.append(current_user_id)

            if set(user_ids_read_message) == set(chat_user_ids):
                message_db: MessageModel = await message_crud.update(db=db,
                                                                     id=message_id,
                                                                     obj_in={'read_at': datetime.now()})
                message: Message = Message.model_validate(message_db)

        case _:
            raise NotImplementedException(log_message=f'Chat type {message.chat.type} not implemented', logger=logger)

    return message
