from aiogram import types, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject

from config import config

router = Router()


@router.message(Command("file_id"))
async def get_file_id(message: types.Message, command: CommandObject):
    if message.reply_to_message and message.reply_to_message.content_type != "text":
        if message.reply_to_message.content_type == "photo":
            return await message.answer(text=message.reply_to_message.photo[-1].file_id)
        await message.answer(
            text=getattr(
                message.reply_to_message, message.reply_to_message.content_type
            ).file_id
        )
    if command.args:
        try:
            try:
                await message.answer_photo(photo=command.args)
            except TelegramBadRequest:
                await message.answer_animation(animation=command.args)
        except Exception as err:
            await message.answer(text=str(err))
    return None


@router.message(Command("reset_counter"))
async def reset_counter(message: types.Message):
    config.counter = 0
    await message.answer(
        text="Готово"
    )


@router.message(Command('err'))
async def error(
        message: types.Message,
):
    qwe = 0 / 0
