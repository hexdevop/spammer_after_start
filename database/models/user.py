import datetime
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, intpk, bigint, created_at



class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]

    user_id: Mapped[bigint] = mapped_column(unique=True)
    ref: Mapped[str | None]
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str]
    lang_code: Mapped[str]
    is_blocked: Mapped[bool] = mapped_column(default=False)

    reg_date: Mapped[created_at]
    death_date: Mapped[datetime.date | None]

    @property
    def link(self):
        if self.username:
            return f"t.me/{self.username}"
        else:
            return f"tg://user?id={self.user_id}"

    @property
    def full_name(self):
        return self.first_name + (self.last_name or "")

    @property
    def mention(self, full_name: bool = False):
        return f'<a href="{self.link}">{self.full_name if full_name else self.first_name}</>'

    def __repr__(self):
        if self.ref is None:
            return f"user: {self.full_name}|@{self.username}|{self.user_id}"
        else:
            return f"user with ref -> [{self.ref}] {self.full_name}|@{self.username}|{self.user_id}"

    __table_args__ = (Index("ix_user_user_id", "user_id"),)
