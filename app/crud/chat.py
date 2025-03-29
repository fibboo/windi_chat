from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, or_, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.chat import Chat, ChatUser
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatRequest, ChatType, ChatUpdate, ChatUserCreate, ChatUserUpdate


class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    async def get_chats(self, db: AsyncSession, request: ChatRequest, current_user_id: int) -> Page[Chat]:
        query: Select = (
            select(self.model)
            .order_by(self.model.created_at)
            .join(ChatUser, self.model.id == ChatUser.chat_id)
            .join(User, ChatUser.user_id == User.id)
            .where(or_(and_(self.model.type == ChatType.GROUP,
                            self.model.name.ilike(f'%{request.search_term}%')),
                       and_(self.model.type == ChatType.PRIVATE,
                            User.id != current_user_id,
                            User.username.ilike(f'%{request.search_term}%'))))
        )

        users: Page[Chat] = await paginate(db, query, request)
        return users


chat_crud = CRUDChat(Chat)


class CRUDChatUser(CRUDBase[ChatUser, ChatUserCreate, ChatUserUpdate]):
    async def get_chat_user_ids(self, db: AsyncSession, chat_id: int) -> list[int]:
        query: Select = select(self.model.user_id).where(self.model.chat_id == chat_id)
        chat_user_ids: list[int] = (await db.scalars(query)).all()
        return chat_user_ids


chat_user_crud = CRUDChatUser(ChatUser)
