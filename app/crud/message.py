from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Message, MessageUserRead
from app.schemas.message import (MessageCreate, MessageRequest, MessageUpdate, MessageUserReadCreate,
                                 MessageUserReadUpdate)


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    async def get_messages(self, db: AsyncSession, chat_id: int, request: MessageRequest) -> Page[Message]:
        query: Select = (select(self.model)
                         .where(self.model.chat_id == chat_id)
                         .order_by(self.model.send_at))

        if request.sender_id is not None:
            query = query.where(self.model.sender_id == request.sender_id)

        if request.search_term is not None:
            query = query.where(self.model.text.ilike(f'%{request.search_term}%'))

        messages: Page[Message] = await paginate(db, query, request)
        return messages


message_crud = CRUDMessage(Message)


class CRUDMessageUserRead(CRUDBase[MessageUserRead, MessageUserReadCreate, MessageUserReadUpdate]):
    async def get_user_ids_read_message(self, db: AsyncSession, message_id: int) -> list[int]:
        query: Select = select(self.model.user_id).where(self.model.message_id == message_id).with_for_update()
        user_ids_read_message: list[int] = (await db.scalars(query)).all()
        return user_ids_read_message


message_user_read_crud = CRUDMessageUserRead(MessageUserRead)
