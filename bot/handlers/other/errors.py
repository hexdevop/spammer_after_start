import os
import traceback

from aiogram import types, Router, html
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from config import config
from database import get_session
from database.models import ErrorLog
from traceback import extract_tb

router = Router()


@router.errors()
async def error_handler(event: types.ErrorEvent):
    # Сохраняем ошибку в БД (накопление)
    try:
        tb_list = extract_tb(event.exception.__traceback__) if event.exception.__traceback__ else []
        last = tb_list[-1] if tb_list else None
        file = None
        line = None
        location = None
        if last:
            print(last)
            file = os.path.relpath(last.filename)
            line = last.lineno
            location = last.name

        exception_class = event.exception.__class__.__name__
        code = getattr(event.exception, 'code', None)
        code = str(code) if code is not None else exception_class
        message = str(event.exception)

        event_ = getattr(event.update, event.update.event_type)
        from_user = getattr(event_, 'from_user', None)
        user_id = getattr(from_user, 'id', None)
        username = getattr(from_user, 'username', None)
        language = getattr(from_user, 'language_code', None)
        chat_id = getattr(getattr(event_, 'chat', None), 'id', None)
        chat = getattr(event_, 'chat', None)
        chat_type_obj = getattr(chat, 'type', None)
        chat_type = (
            getattr(chat_type_obj, 'value', None)
            if chat_type_obj is not None and hasattr(chat_type_obj, 'value')
            else (str(chat_type_obj) if chat_type_obj is not None else None)
        )
        update_type = event.update.event_type

        trace_text = traceback.format_exc()

        async with get_session() as session:
            async with session.begin():
                session.add(
                    ErrorLog(
                        code=code,
                        exception_class=exception_class,
                        message=message,
                        file=file,
                        location=location,
                        line=line,
                        user_id=user_id,
                        username=username,
                        language=language,
                        chat_id=chat_id,
                        chat_type=chat_type,
                        update_type=update_type,
                        trace=trace_text,
                    )
                )
        logger.error(f"Captured error [{code}] {exception_class} at {file}:{line} ({location})")

    except Exception as e:
        logger.exception(f"Failed to persist error: {e}")

    if config.error_notification:
        exception_class = event.exception.__class__

        # if exception_class not in [TelegramBadRequest, DataError]:
        #     raise event.exception
        #     return

        bot = event.update.bot
        error_traceback = traceback.format_exc().encode("utf-8")
        file = types.BufferedInputFile(error_traceback, filename="error.txt")

        event_ = getattr(event.update, event.update.event_type)
        postfix = f"\n\nОшибка от пользователя <code>{event_.from_user.id}</>\nСписок всех ошибок: /errors"
        try:
            await bot.send_document(
                chat_id=491264374,
                document=file,
                caption=f"<code>{html.quote(str(exception_class))}: {html.quote(str(event.exception))}</>{postfix}",
            )
        except TelegramBadRequest:
            await bot.send_document(
                chat_id=491264374,
                document=file,
                caption=f"<code>{html.quote(str(exception_class))}</>{postfix}",
            )
