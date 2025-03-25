from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket

from app.api.deps import get_db, get_db_transaction, get_device_id_ws, get_user_id, get_user_id_ws
from app.schemas.chat import Chat, ChatRequest
from app.schemas.message import Message, MessageRequest
from app.services import chat_service, message_service

router = APIRouter()


@router.websocket('/ws/{chat_id}')
async def connect_to_chat(chat_id: int,
                          websocket: WebSocket,
                          current_user_id: int = Depends(get_user_id_ws),
                          device_id: str = Depends(get_device_id_ws),
                          db: AsyncSession = Depends(get_db)) -> None:
    await chat_service.connect_to_chat(db=db,
                                       websocket=websocket,
                                       chat_id=chat_id,
                                       current_user_id=current_user_id,
                                       device_id=device_id)


@router.get('')
async def get_chats(request: ChatRequest = Depends(),
                    current_user_id: int = Depends(get_user_id),
                    db: AsyncSession = Depends(get_db)) -> Page[Chat]:
    chats: Page[Chat] = await chat_service.get_chats(db=db, request=request, current_user_id=current_user_id)
    return chats


@router.post('/private/{user_id}')
async def create_private_chat(user_id: int,
                              current_user_id: int = Depends(get_user_id),
                              db: AsyncSession = Depends(get_db_transaction)) -> Chat:
    chat: Chat = await chat_service.create_private_chat(db=db,
                                                        user_id=user_id,
                                                        current_user_id=current_user_id)
    return chat


@router.get('/{chat_id}')
async def get_chat(chat_id: int,
                   db: AsyncSession = Depends(get_db)) -> Chat:
    chat: Chat = await chat_service.get_chat(db=db, chat_id=chat_id)
    return chat


@router.get('/{chat_id}/history')
async def get_messages(chat_id: int,
                       request: MessageRequest = Depends(),
                       _: int = Depends(get_user_id),
                       db: AsyncSession = Depends(get_db)) -> Page[Message]:
    messages: Page[Message] = await message_service.get_messages(db=db,
                                                                 chat_id=chat_id,
                                                                 request=request)
    return messages
