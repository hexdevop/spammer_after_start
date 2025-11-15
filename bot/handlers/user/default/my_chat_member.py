import datetime

from aiogram import types, Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, KICKED
from fluent.runtime import FluentLocalization
from sqlalchemy import update

from database import get_session
from database.models import User
from bot.services import PostManager

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> KICKED))
async def handle_user_block_bot(
    event: types.ChatMemberUpdated,
    post_manager: PostManager,
):
    async with get_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(User.user_id == event.from_user.id)
                .values(is_blocked=True, death_date=datetime.datetime.now())
            )
    post_manager.stop_user_spam(event.from_user.id)


@router.my_chat_member(ChatMemberUpdatedFilter(KICKED >> IS_MEMBER))
async def handle_user_unblock_bot(
    event: types.ChatMemberUpdated, l10n: FluentLocalization
):
    await event.bot.send_message(
        chat_id=event.from_user.id, text=l10n.format_value("dont-block-anymore")
    )
