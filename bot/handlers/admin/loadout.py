import datetime
from io import BytesIO

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluent.runtime import FluentLocalization
from sqlalchemy import select, func

from database import get_session
from database.models import User
from bot.keyboards.admin import inline
from bot.keyboards.admin.factory import LoadOutCallbackData

router = Router()
buttons = {
    "order": {
        "begin": "⏮ Старые",
        "random": "🔀 Рандом",
        "end": "Свежих ⏭",
    },
}

@router.message(F.text == "Выгрузка 🗳")
async def load_out(
        message: types.Message,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await state.clear()
    selected = {
        "order": "random",
    }
    await message.answer(
        text=l10n.format_value(
            "load-out",
            {
                "order": buttons["order"][selected["order"]],
            },
        ),
        reply_markup=inline.load_out(buttons, selected),
    )
    await state.update_data(selected=selected)


@router.callback_query(LoadOutCallbackData.filter(F.action != "start"))
async def select_settings(
        call: types.CallbackQuery,
        callback_data: LoadOutCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    data = await state.get_data()
    selected = data["selected"]
    selected["order"] = callback_data.action
    await call.message.edit_text(
        text=l10n.format_value(
            "load-out",
            {
                "order": buttons["order"][selected["order"]],
            },
        ),
        reply_markup=inline.load_out(buttons, selected),
    )
    await state.update_data(selected=selected)


@router.callback_query(LoadOutCallbackData.filter(F.action == "start"))
async def start_load_outing_audit(
        call: types.CallbackQuery,
        state: FSMContext,
        scheduler: AsyncIOScheduler,
        l10n: FluentLocalization,
):
    data = await state.get_data()
    selected = data["selected"]
    job = scheduler.get_job("load-out")
    if job is None:
        scheduler.add_job(
            id="load-out",
            func=load_outing,
            trigger="date",
            run_date=datetime.datetime.now() + datetime.timedelta(seconds=1),
            kwargs={"bot": call.bot, "l10n": l10n, "selected": selected, "admin_id": call.from_user.id, "message_id": call.message.message_id}
        )
    else:
        await call.message.edit_text(text=l10n.format_value("load-out-already-doing"))


async def load_outing(
        bot: Bot,
        l10n: FluentLocalization,
        selected: dict,
        admin_id: int,
        message_id: int,
):
    message_to_delete = await bot.edit_message_text(
        chat_id=admin_id,
        text=l10n.format_value(
            "start-load-out",
            {
                "order": buttons["order"][selected["order"]],
            },
        ),
        message_id=message_id,
    )
    async with get_session() as session:
        scope = (
            await session.scalars(
                select(User.user_id)
                .where(User.is_blocked.is_(False))
                .order_by({
                    "begin": User.id,
                    "end": User.id.desc(),
                    "random": func.random(),
                }.get(selected['order']))
            )
        ).all()

    scope_str = "\n".join(map(str, scope))
    file = BytesIO(scope_str.encode("utf-8"))
    file.seek(0)
    await message_to_delete.delete()
    await bot.send_document(
        chat_id=admin_id,
        document=types.BufferedInputFile(file.getvalue(), filename="scope.txt"),
        caption=l10n.format_value(
            "load-out-results",
            {
                "order": buttons["order"][selected["order"]],
                "count": len(scope),
            },
        ),
    )
