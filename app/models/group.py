from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.chat import Chat
from app.models.user import User


class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False)

    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey(Chat.id), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(),
                                                 nullable=False)
