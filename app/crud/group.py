from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Group
from app.schemas.group import GroupCreate, GroupRequest, GroupUpdate


class CRUDGroup(CRUDBase[Group, GroupCreate, GroupUpdate]):
    async def get_groups(self, db: AsyncSession, request: GroupRequest) -> Page[Group]:
        query: Select = (select(self.model)
                         .where(self.model.name.ilike(f'%{request.search_term}%'))
                         .order_by(self.model.created_at.desc()))

        groups: Page[Group] = await paginate(db, query, request)
        return groups


group_crud = CRUDGroup(Group)
