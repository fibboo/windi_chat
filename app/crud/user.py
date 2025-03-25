from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User
from app.models.chat import ChatUser
from app.schemas.user import UserCreateRequest, UserRequest, UserUpdate


class CRUDUser(CRUDBase[User, UserCreateRequest, UserUpdate]):
    async def get_users(self, db: AsyncSession, request: UserRequest, current_user_id: int | None):
        query: Select = select(self.model).order_by(self.model.created_at)

        if request.search_term is not None:
            query = query.where(self.model.username.ilike(f'%{request.search_term}%'))

        if current_user_id is not None:
            query = query.where(self.model.id != current_user_id)

        if request.chat_id is not None:
            query = query.join(ChatUser, self.model.id == ChatUser.user_id).where(ChatUser.chat_id == request.chat_id)

        users: Page[User] = await paginate(db, query, request)
        return users


user_crud = CRUDUser(User)
