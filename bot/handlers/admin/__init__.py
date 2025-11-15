from aiogram import Dispatcher
from loguru import logger

from . import (
    mover,
    statistic,
    loadout,
    referral,
    sql,
    commands,
    errors,
    spam,
)
from bot.filters.admin import AdminFilter


def reg_routers(dp: Dispatcher):
    handlers = [
        mover,
        statistic,
        loadout,
        referral,
        sql,
        commands,
        errors,
        spam
    ]
    for handler in handlers:
        handler.router.message.filter(AdminFilter())
        dp.include_router(handler.router)
    logger.opt(colors=True).info(
        f"<fg #ffb4aa>[admin {len(handlers)} handlers imported]</>"
    )
