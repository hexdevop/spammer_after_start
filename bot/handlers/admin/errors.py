from aiogram import types, Router, F
from aiogram.filters import Command
from fluent.runtime import FluentLocalization
from sqlalchemy import select, func, delete
from loguru import logger

from bot.keyboards.admin import inline
from config import config
from database import get_session
from database.models import ErrorLog
from bot.keyboards.admin.factory import ErrorsCallbackData

router = Router()


@router.message(Command("errors", magic=F.text.split().len() == 1))
async def errors_list(
        event: types.Message | types.CallbackQuery,
        l10n: FluentLocalization,
        edit: bool = False,
        page: int = 1,
):
    async with get_session() as session:
        rows = (await session.execute(
            select(
                ErrorLog.code.label("code"),
                ErrorLog.location.label("location"),
                func.count(ErrorLog.id).label("count"),
                func.max(ErrorLog.id).label("latest_id"),
            )
            .group_by(ErrorLog.code, ErrorLog.location)
            .order_by(func.count(ErrorLog.id).desc())
            .limit(10).offset((page - 1) * 10)
        )).all()
    message = event.message if isinstance(event, types.CallbackQuery) else event
    method = message.edit_text if edit else message.answer
    await method(
        text=l10n.format_value("errors-title"),
        reply_markup=inline.errors_list(rows, page=1),
    )


@router.callback_query(ErrorsCallbackData.filter(F.action == "error"))
async def error_detail(
        call: types.CallbackQuery,
        callback_data: ErrorsCallbackData,
        l10n: FluentLocalization
):
    async with get_session() as session:
        error = await session.scalar(
            select(ErrorLog).where(ErrorLog.id == callback_data.id)
        )
        total_count: int = await session.scalar(select(func.count()).where(ErrorLog.id == callback_data.id)) or 0
    if not error:
        await call.answer("Нет данных", show_alert=True)
        return

    await call.message.delete()
    await call.message.answer_document(
        document=types.BufferedInputFile(error.trace.encode("utf-8"), filename=f"Error_{error.code}_{error.message}.txt"),
        caption=l10n.format_value(
        "errors-detail",
        {
            "code": error.code,
            "exception_class": error.exception_class,
            "message": error.message,
            "created_at": error.created_at,
            "update_type": error.update_type.capitalize(),
            "user_id": str(error.user_id),
            "username": f"@{error.username}",
            "language": error.language,
            "chat_id": str(error.chat_id),
            "chat_type": error.chat_type.upper(),
            "file": error.file,
            "line": error.line,
            "location": error.location,
            "count": total_count,
        },
    ),
        reply_markup=inline.back(callback_data, l10n, 'page')
    )


@router.callback_query(ErrorsCallbackData.filter(F.action == "fixed"))
async def fix_error(
        call: types.CallbackQuery,
        callback_data: ErrorsCallbackData,
        l10n: FluentLocalization,
):
    async with get_session() as session:
        async with session.begin():
            # Найдём одну запись, чтобы взять её код ошибки
            error = await session.scalar(select(ErrorLog).where(ErrorLog.id == callback_data.id))
            if not error:
                await call.answer(l10n.format_value("errors-not-found"), show_alert=True)
                return

            result = await session.execute(
                delete(ErrorLog).where(
                    ErrorLog.code == error.code,
                    ErrorLog.location == callback_data.location,
                )
            )

        deleted = result.rowcount or 0
        logger.success(f"Deleted {deleted} ErrorLog rows for code={error.code} location={callback_data.location}")

        await call.answer(l10n.format_value("errors-fixed-alert"), show_alert=True)
        await errors_list(call, l10n, edit=True, page=callback_data.page)



@router.callback_query(ErrorsCallbackData.filter(F.action == "status"))
async def status(
        call: types.CallbackQuery,
        callback_data: ErrorsCallbackData,
        l10n: FluentLocalization,
):
    config.error_notification = not config.error_notification
    await pagination(call, callback_data, l10n)


@router.callback_query(ErrorsCallbackData.filter(F.action == "page"))
async def pagination(
        call: types.CallbackQuery,
        callback_data: ErrorsCallbackData,
        l10n: FluentLocalization,
):
    if call.message.document:
        await call.message.delete()
        await errors_list(call, l10n, edit=False, page=callback_data.page)
    else:
        await errors_list(call, l10n, edit=True, page=callback_data.page)
