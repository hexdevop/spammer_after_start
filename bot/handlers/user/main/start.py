from aiogram import types, Router, F, html

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from loguru import logger
from sqlalchemy import select, update

from bot.utils import helper
from config import config
from database import get_session
from database.models import User, Ref
from bot.keyboards.user import reply

from bot.services import PostManager

router = Router(name="start")


@router.message(Command("start", magic=F.text.split().len() == 1))
async def start_command(
    message: types.Message,
    state: FSMContext,
    l10n: FluentLocalization,
    post_manager: PostManager,
    ref: str = None,
):
    await state.clear()
    await process_user(message.from_user, ref)
    if message.from_user.id not in config.admins:
        post_manager.start_user_spam(message.from_user.id)
    await message.answer(
        text=l10n.format_value("start"),
        reply_markup=reply.main_menu(l10n, message.from_user.id in config.admins),
    )
    await helper.send_hi_views(message.from_user.id, message.message_id, message.from_user.first_name, message.from_user.language_code, startplace=True)


async def process_user(
    from_user: types.User,
    ref: str = None,
):
    async with get_session() as session:
        async with session.begin():
            if ref:
                await session.execute(
                    update(Ref).where(Ref.name == ref).values(follows=Ref.follows + 1)
                )
            is_blocked = await session.scalar(
                select(User.is_blocked).where(User.user_id == from_user.id)
            )
            if is_blocked is None:
                user = User(
                    user_id=from_user.id,
                    ref=ref,
                    first_name=html.quote(from_user.first_name),
                    last_name=(
                        html.quote(from_user.last_name) if from_user.last_name else None
                    ),
                    username=from_user.username,
                    lang_code=from_user.language_code,
                )
                session.add(user)
                logger.success(f"Register new {user}")
            else:
                params = {
                    "first_name": html.quote(from_user.first_name),
                    "username": from_user.username,
                }
                if from_user.last_name:
                    params["last_name"] = html.quote(from_user.last_name)
                if is_blocked:
                    params["is_blocked"] = False
                await session.execute(
                    update(User).where(User.user_id == from_user.id).values(**params)
                )
