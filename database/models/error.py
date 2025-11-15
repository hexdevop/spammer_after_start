from sqlalchemy import Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, intpk, created_at


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id: Mapped[intpk]

    code: Mapped[str]
    exception_class: Mapped[str]
    message: Mapped[str]

    file: Mapped[str | None]
    location: Mapped[str | None]  # module:function
    line: Mapped[int | None]

    user_id: Mapped[int | None] = mapped_column(BigInteger)
    username: Mapped[str | None]
    language: Mapped[str | None]
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    chat_type: Mapped[str | None]
    update_type: Mapped[str | None]

    trace: Mapped[str] = mapped_column(Text)

    created_at: Mapped[created_at]

    def __repr__(self):
        return f"ErrorLog[{self.code}] {self.exception_class} at {self.file}:{self.line} ({self.location})"