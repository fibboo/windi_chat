from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, func, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID

from app.models.base import Base
from app.models.chat import Chat
from app.models.user import User


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[UUID] = mapped_column(DB_UUID, primary_key=True)  # noqa: A003
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey(Chat.id), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False)
    text: Mapped[str] = mapped_column(String(4096), nullable=False)

    chat: Mapped[Chat] = relationship(Chat, foreign_keys=[chat_id], lazy='selectin')

    send_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(),
                                                 nullable=False)


class MessageUserRead(Base):
    __tablename__ = 'message_users_read'
    __table_args__ = (UniqueConstraint('message_id', 'user_id', name='message_user_read_unique'),)

    message_id: Mapped[UUID] = mapped_column(DB_UUID, ForeignKey(Message.id), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), primary_key=True)
