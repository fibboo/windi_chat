from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.user import User
from app.schemas.chat import ChatType


class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType,  # noqa: A003
                                                native_enum=False,
                                                validate_strings=True,
                                                values_callable=lambda x: [i.value for i in x]),
                                           nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(),
                                                 nullable=False)


class ChatUser(Base):
    __tablename__ = 'chat_users'
    __table_args__ = (UniqueConstraint('chat_id', 'user_id', name='chat_user_unique'),)

    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey(Chat.id), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
