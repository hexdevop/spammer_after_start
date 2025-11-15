from aiogram import types, Router

from bot.filters.buttons import Button
# from bot.services import PostManager
from bot.utils import helper
from config import config

router = Router()


@router.message(Button('button'))
async def button(
        message: types.Message,
        # post_manager: PostManager,
):
    # post_manager.stop_user_spam(message.from_user.id)
    config.counter += 1
    await helper.send_hi_views(message.from_user.id, message.message_id, message.from_user.first_name, message.from_user.language_code, startplace=False)