from typing import Any

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, intpk, created_at, updated_at

from bot.enums import MediaType, Status



class Ref(Base):
    __tablename__ = "refs"

    id: Mapped[intpk]

    name: Mapped[str]
    price: Mapped[int] = mapped_column(default=0)
    follows: Mapped[int] = mapped_column(default=0)
    chat_follows: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]



class Post(Base):
    __tablename__ = "posts"

    id: Mapped[intpk]

    media_type: Mapped[MediaType]
    media: Mapped[str | None]
    text: Mapped[str] = mapped_column(Text)
    reply_markup: Mapped[dict[str, Any]]

    status: Mapped[Status] = mapped_column(default=Status.WORKING)

    sent: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
