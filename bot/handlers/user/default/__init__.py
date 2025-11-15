from aiogram import Dispatcher
from aiogram.enums import ChatType
from loguru import logger


from . import (
    my_chat_member,
)
from bot.filters.chat_type import ChatTypeFilter


def reg_routers(dp: Dispatcher):
    handlers = [
        my_chat_member,
    ]
    for handler in handlers:
        handler.router.message.filter(ChatTypeFilter(ChatType.PRIVATE))

        dp.include_router(handler.router)
    logger.opt(colors=True).info(
        f"<fg #abffaa>[user.default {len(handlers)} files imported]</>"
    )
