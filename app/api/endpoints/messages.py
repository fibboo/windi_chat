from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_db_transaction, get_device_id, get_user_id
from app.schemas.message import Message, MessageCreateRequest
from app.services import message_service

router = APIRouter()


@router.post('')
async def send_message(create_data: MessageCreateRequest,
                       current_user_id: int = Depends(get_user_id),
                       device_id: str = Depends(get_device_id),
                       db: AsyncSession = Depends(get_db_transaction)) -> Message:
    message: Message = await message_service.send_message(db=db,
                                                          create_data=create_data,
                                                          current_user_id=current_user_id,
                                                          device_id=device_id)
    return message


@router.get('/{message_id}')
async def get_message(message_id: UUID,
                      _: int = Depends(get_user_id),
                      db: AsyncSession = Depends(get_db)) -> Message:
    message: Message = await message_service.get_message(db=db, message_id=message_id)
    return message
