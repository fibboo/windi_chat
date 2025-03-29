import asyncio

from fastapi_pagination import Page
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets import ConnectionClosedError, ConnectionClosedOK

from app.configs.logging_settings import get_logger
from app.crud.chat import chat_crud, chat_user_crud
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.forbidden_403 import UserNotChatMemberException
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.chat import Chat as ChatModel, ChatUser as ChatUserModel
from app.schemas.chat import Chat, ChatCreate, ChatRequest, ChatType, ChatUserCreate
from app.schemas.message import MessageRead
from app.services import message_service
from app.services.websocket_manager import websocket_manager

logger = get_logger(__name__)


async def connect_to_chat(db: AsyncSession,
                          websocket: WebSocket,
                          chat_id: int,
                          current_user_id: int,
                          device_id: str):
    await get_chat(db=db, chat_id=chat_id, current_user_id=current_user_id)
    await websocket_manager.connect(websocket=websocket, chat_id=chat_id, user_id=current_user_id, device_id=device_id)

    try:
        while True:
            await asyncio.sleep(1)
            message_read_dict: dict = await websocket.receive_json()
            try:
                message_read: MessageRead = MessageRead(**message_read_dict)
                await message_service.read_message(db=db,
                                                   message_id=message_read.message_id,
                                                   current_user_id=current_user_id)
            except Exception as exc:
                logger.error(f'Error while read message: {exc}')
                continue

    except (ConnectionClosedOK, RuntimeError, WebSocketDisconnect, ConnectionClosedError):
        websocket_manager.disconnect(chat_id=chat_id, user_id=current_user_id, device_id=device_id)


async def get_chats(db: AsyncSession, request: ChatRequest, current_user_id: int) -> Page[Chat]:
    chats_db: Page[ChatModel] = await chat_crud.get_chats(db=db, request=request, current_user_id=current_user_id)
    chats: Page[Chat] = Page[Chat].model_validate(chats_db)
    return chats


async def create_chat(db: AsyncSession, create_data: ChatCreate) -> Chat:
    try:
        chat_db: ChatModel = await chat_crud.create(db=db, obj_in=create_data)

    except IntegrityError as exc:
        raise IntegrityException(entity=ChatModel, exception=exc, logger=logger)

    chat: Chat = Chat.model_validate(chat_db)
    return chat


async def create_chat_users(db: AsyncSession, chat_id: int, user_ids: list[int]) -> None:
    chat_users_create: list[ChatUserCreate] = [ChatUserCreate(chat_id=chat_id, user_id=user_id) for user_id in user_ids]
    try:
        await chat_user_crud.create_batch(db=db, objs_in=chat_users_create)

    except IntegrityError as exc:
        raise IntegrityException(entity=ChatUserModel, exception=exc, logger=logger)


async def create_private_chat(db: AsyncSession, user_id: int, current_user_id: int) -> Chat:
    users_ids: list[int] = [user_id, current_user_id]
    users_ids.sort()

    create_data: ChatCreate = ChatCreate(name=f'Private-{users_ids}', type=ChatType.PRIVATE)
    chat: Chat = await create_chat(db=db, create_data=create_data)

    await create_chat_users(db=db, chat_id=chat.id, user_ids=users_ids)

    return chat


async def get_chat(db: AsyncSession, chat_id: int, current_user_id: int) -> Chat:
    chat_db: ChatModel | None = await chat_crud.get_or_none(db=db, id=chat_id)
    if chat_db is None:
        raise EntityNotFound(entity=ChatModel, search_params={'id': chat_id}, logger=logger)

    chat_user_ids: list[int] = await chat_user_crud.get_chat_user_ids(db=db, chat_id=chat_db.id)
    if current_user_id not in chat_user_ids:
        raise UserNotChatMemberException(user_id=current_user_id, chat_id=chat_db.id, logger=logger)

    chat: Chat = Chat.model_validate(chat_db)
    return chat
