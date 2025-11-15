import datetime
import re
import string
import random

import aiohttp
from aiogram import types, exceptions, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message
from loguru import logger

from config import config


class Plug:
    message_id = 000


async def send_media_group(bot: Bot, chat_id: int, media: list):
    try:
        return await bot.send_media_group(chat_id=chat_id, media=media)
    except TelegramBadRequest:
        return [Plug()]


async def send_message(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup = None,
):
    try:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )
    except (TelegramBadRequest, TelegramForbiddenError):
        return Plug()


async def edit_message_text(bot: Bot, chat_id: int, text: str, message_id: int):
    try:
        return await bot.edit_message_text(
            chat_id=chat_id, text=text, message_id=message_id
        )
    except TelegramBadRequest:
        return None


def break_time(last_time: datetime, hours: int = 4):
    total_seconds = (
        datetime.timedelta(hours=hours) - (datetime.datetime.now() - last_time)
    ).total_seconds()
    hours = int((total_seconds // 60) // 60)
    minutes = int((total_seconds // 60) % 60)
    seconds = int(total_seconds % 60)
    return hours, minutes, seconds


def is_days_passed(date: datetime.date, days: int = 1) -> bool:
    if date is None:
        return True
    try:
        return datetime.datetime.now() >= date + datetime.timedelta(days=days)
    except TypeError:
        return datetime.date.today() >= date + datetime.timedelta(days=days)


def is_time_passed(last_time: datetime, hours: int = 4) -> bool:
    if last_time is None:
        return True
    try:
        return datetime.datetime.now() - last_time >= datetime.timedelta(hours=hours)
    except TypeError:
        return datetime.date.today() - last_time >= datetime.timedelta(hours=hours)


async def send_media(
    media: str,
    caption: str,
    bot: Bot = None,
    event: types.Message | types.CallbackQuery = None,
    reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup = None,
    user_id: int = None,
    is_photo: bool = True,
    has_spoiler: bool = False,
) -> types.Message | Plug:
    if not bot:
        bot = event.bot
    user_id = user_id or event.from_user.id
    try:
        if is_photo:
            response = await bot.send_photo(
                chat_id=user_id,
                photo=media,
                caption=caption,
                reply_markup=reply_markup,
                has_spoiler=has_spoiler,
            )
        else:
            response = await bot.send_video(
                chat_id=user_id,
                video=media,
                caption=caption,
                reply_markup=reply_markup,
                has_spoiler=has_spoiler,
            )
    except TelegramBadRequest:
        return Plug()
    return response


async def edit_media(
    event: types.Message | types.CallbackQuery,
    media: str,
    caption: str,
    reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup = None,
    user_id: int = None,
    is_photo: bool = True,
    has_spoiler: bool = False,
) -> Message | bool | Plug:
    bot = event.bot
    message = event if isinstance(event, types.Message) else event.message
    user_id = user_id or event.from_user.id
    if is_photo:
        input_type = types.InputMediaPhoto
    else:
        input_type = types.InputMediaVideo
    try:
        return await bot.edit_message_media(
            media=input_type(media=media, caption=caption, has_spoiler=has_spoiler),
            chat_id=user_id,
            message_id=message.message_id,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest:
        return Plug()


def nearest_multiples(number: int, nearest: int = 2):
    lower = int(number // nearest) * nearest
    upper = lower + nearest
    return lower, upper


def get_percent(all_count: int, count: int) -> int:
    return round((count / all_count) * 100) if all_count else 0


async def delete_messages(
    event: types.Message | types.CallbackQuery, data: dict = None, user_id: int = None
):
    try:
        if isinstance(event, types.Message):
            message_ids = [event.message_id]
        else:
            message_ids = [event.message.message_id]
        if data:
            message_ids += data.get("message_ids", [])
            if "message_id" in data.keys():
                message_ids.append(data.get("message_id"))
        await event.bot.delete_messages(
            chat_id=user_id or event.from_user.id, message_ids=message_ids
        )
    except exceptions.TelegramBadRequest:
        pass


async def delete_message(bot: Bot, user_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id=user_id, message_id=message_id)
    except exceptions.TelegramBadRequest:
        pass


def generate_symbols(length: int = 7, use_numbers: bool = True):
    characters = (
        string.ascii_letters + string.digits if use_numbers else string.ascii_letters
    )
    return "".join(random.choice(characters) for _ in range(length))


def has_cyrillic(text):
    return bool(re.search("[а-яА-Я]", text))


async def send_hi_views(
        user_id: int,
        message_id: int,
        user_first_name: str,
        language_code: str,
        startplace: bool
):
    if config.hiviews is not None and config.hiviews != '':
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    'https://hiviews.net/sendMessage',
                    headers={
                        'Authorization': config.hiviews,
                        'Content-Type': 'application/json',
                    },
                    json={
                        'UserId': user_id,
                        'MessageId': message_id,
                        'UserFirstName': user_first_name,
                        'LanguageCode': language_code,
                        'StartPlace': startplace
                    },
            ) as response:
                logger.info(f"[HiViews] {await response.text('utf-8')}")
    else:
        logger.warning("You should add HiViews' token before calling this function")
