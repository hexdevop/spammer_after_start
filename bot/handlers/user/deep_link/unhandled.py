from aiogram import types, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization

from bot.handlers.user.main.start import start_command
from bot.services import PostManager

router = Router()


@router.message(CommandStart(deep_link=True))
async def deep_links(
    message: types.Message,
    command: CommandObject,
    state: FSMContext,
    l10n: FluentLocalization,
    post_manager: PostManager,
):
    await state.clear()
    await start_command(message, state, l10n, post_manager=post_manager, ref=command.args)
