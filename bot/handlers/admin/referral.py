import matplotlib.pyplot as plt
from io import BytesIO
import datetime
import numpy as np

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database import get_session
from database.models import Ref, User
from bot.keyboards.admin import reply, inline
from bot.keyboards.admin.factory import RefCallbackData
from bot.states import RefState
from bot.utils import helper


router = Router()


@router.message(F.text == "Создать реф. ссылку 🆕")
async def referral_menu(
        message: types.Message,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await state.clear()
    message_id = (
        await message.answer(
            text=l10n.format_value("get-new-referral-name"),
            reply_markup=reply.generate_new_ref(),
        )
    ).message_id
    await state.update_data(message_id=message_id)
    await state.set_state(RefState.name)


@router.message(RefState.name, F.text)
async def get_ref_name(
        message: types.Message,
        state: FSMContext,
        l10n: FluentLocalization,
):
    data = await state.get_data()
    await helper.delete_messages(message, data)
    if message.text == "Сгенерировать ✍️":
        name = helper.generate_symbols()
    else:
        name = message.text
    if not helper.has_cyrillic(name):
        message_id = (
            await message.answer(
                text=l10n.format_value("get-price-for-ref"),
                reply_markup=reply.skip_and_cancel(),
            )
        ).message_id
        await state.update_data(message_id=message_id)
        await state.update_data(name=name)
        await state.set_state(RefState.price)
    else:
        message_id = (
            await message.answer(
                text=l10n.format_value("your-ref-has-cyrillic-symbols"),
                reply_markup=reply.generate_new_ref(),
            )
        ).message_id
        await state.update_data(message_id=message_id)


@router.message(RefState.price, F.text)
async def get_ref_price(
        message: types.Message,
        state: FSMContext,
        l10n: FluentLocalization,
):
    data = await state.get_data()
    await helper.delete_messages(message, data)
    is_digit = message.text.isdigit()
    async with get_session() as session:
        async with session.begin():
            if "callback_data" in data:
                callback_data = RefCallbackData.model_validate(data["callback_data"])

                if not is_digit:
                    message_id = (
                        await message.answer(
                            text=l10n.format_value("its-not-digit"),
                            reply_markup=inline.cancel(callback_data, "settings"),
                        )
                    ).message_id
                    return await state.update_data(message_id=message_id)

                price = int(message.text)
                await session.execute(
                    update(Ref).where(Ref.id == callback_data.id).values(price=price)
                )
                await referral_settings(message, callback_data, state, l10n)

            else:
                if not is_digit and message.text != "Пропустить ⏭":
                    message_id = (
                        await message.answer(
                            text=l10n.format_value("its-not-digit"),
                            reply_markup=reply.skip_and_cancel(),
                        )
                    ).message_id
                    return await state.update_data(message_id=message_id)

                price = int(message.text) if is_digit else None
                session.add(Ref(name=data.get("name"), price=price))

                await message.answer(
                    text=l10n.format_value("ref-successfully-created"),
                    reply_markup=reply.referral_menu(),
                )
                await state.clear()


@router.message(F.text == "Список реф. ссылок 📋")
async def referral_list(
        event: types.Message | types.CallbackQuery,
        state: FSMContext,
        l10n: FluentLocalization,
        edit: bool = False,
        page: int = 1,
):
    await state.clear()
    async with get_session() as session:
        refs = (await session.scalars(select(Ref))).all()
    message = event if isinstance(event, types.Message) else event.message
    method = message.edit_text if edit else message.answer
    await method(
        text=l10n.format_value(
            "referral-list" if len(refs) > 0 else "referral-list-empty"
        ),
        reply_markup=inline.refs_list(refs, page=page),
    )


@router.callback_query(RefCallbackData.filter(F.action == "main"))
async def main(
        call: types.CallbackQuery,
        callback_data: RefCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await referral_list(call, state, l10n, edit=True, page=callback_data.page)


@router.callback_query(RefCallbackData.filter(F.action == "settings"))
async def referral_settings(
        event: types.CallbackQuery | types.Message,
        callback_data: RefCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await state.clear()
    async with get_session() as session:
        ref: Ref = await session.scalar(select(Ref).where(Ref.id == callback_data.id))
        params = await get_params(session, ref)
    method = (
        event.answer if isinstance(event, types.Message) else event.message.edit_text
    )
    await method(
        text=l10n.format_value('referral-user-stats', params),
        reply_markup=inline.referral_settings(callback_data),
    )


@router.callback_query(RefCallbackData.filter(F.action == "price"))
async def change_price(
        call: types.CallbackQuery,
        callback_data: RefCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await state.clear()
    message_id = (
        await call.message.edit_text(
            text=l10n.format_value("get-price-for-ref"),
            reply_markup=inline.cancel(callback_data, "settings"),
        )
    ).message_id
    await state.update_data(message_id=message_id)
    await state.update_data(callback_data=callback_data.model_dump())
    await state.set_state(RefState.price)


@router.callback_query(RefCallbackData.filter(F.action == "graph"))
async def get_graph(
        call: types.CallbackQuery,
        callback_data: RefCallbackData,
):
    async with get_session() as session:
        ref = await session.scalar(select(Ref).where(Ref.id == callback_data.id))
        image_stream = await generate_statistic_graph(session, ref)
    await call.message.answer_photo(
        photo=types.BufferedInputFile(image_stream.getvalue(), filename="graph.jpg")
    )


@router.callback_query(RefCallbackData.filter(F.action == "delete"))
async def delete_referral(
        call: types.CallbackQuery,
        callback_data: RefCallbackData,
        l10n: FluentLocalization,
):
    await call.message.edit_text(
        text=l10n.format_value("confirm-deleting"),
        reply_markup=inline.confirm(callback_data, cancel_value="settings"),
    )


@router.callback_query(RefCallbackData.filter(F.action == "confirm"))
async def confirm_deleting(
        call: types.CallbackQuery,
        callback_data: RefCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    async with get_session() as session:
        async with session.begin():
            await session.execute(delete(Ref).where(Ref.id == callback_data.id))
    await call.message.edit_text(text=l10n.format_value("successfully-deleted"))
    await referral_list(call, state, l10n, edit=False, page=callback_data.page)


@router.callback_query(RefCallbackData.filter(F.action == "page"))
async def pagination(
        call: types.CallbackQuery,
        callback_data: RefCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await referral_list(call, state, l10n, edit=True, page=callback_data.page)
    await call.answer(text=l10n.format_value("page", {"page": callback_data.page}))


@router.callback_query(RefCallbackData.filter(F.action == "length"))
async def length_of_list(
        call: types.CallbackQuery,
        l10n: FluentLocalization,
):
    await call.answer(text=l10n.format_value("length-of-list"), show_alert=True)


async def get_params(session: AsyncSession, ref: Ref):
    total = await session.scalar(count(User, User.ref == ref.name))
    active = await session.scalar(
        count(User, User.ref == ref.name, User.is_blocked.is_(False))
    )
    params = {"name": ref.name, "username": config.bot.username, "price": "{:.1f}".format(ref.price), "total": total,
              "total_price": "{:.1f}".format(calculate_price(ref.price, total)), "active": active,
              "active_percent": helper.get_percent(total, active),
              "active_price": "{:.1f}".format(calculate_price(ref.price, active)), "follows": ref.follows,
              "follows_price": "{:.1f}".format(
                  calculate_price(ref.price, ref.follows)
              )}

    day = datetime.date.today()

    today = await session.scalar(
        count(User, User.ref == ref.name, User.reg_date >= day)
    )
    week = await session.scalar(
        count(
            User,
            User.ref == ref.name,
            User.reg_date >= day - datetime.timedelta(days=6),
        )
    )
    month = await session.scalar(
        count(
            User,
            User.ref == ref.name,
            User.reg_date >= day - datetime.timedelta(days=30),
        )
    )
    params["today"] = today
    params["week"] = week
    params["month"] = month
    return params


def format_number(num):
    if num >= 1000000:
        return f"{num / 1000000:.1f}М"
    elif num >= 1000:
        return f"{num / 1000:.1f}к"
    else:
        return str(num)


async def generate_statistic_graph(
        session: AsyncSession,
        ref: Ref,
):
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=30)
    dates = [start_date + datetime.timedelta(days=i) for i in range(31)]

    total_counts = [0] * 31
    active_counts = [0] * 31

    for i, date in enumerate(dates):
        total_counts[i] = await session.scalar(
            count(User, User.ref == ref.name, User.reg_date == date)
        )
        active_counts[i] = await session.scalar(
            count(
                User,
                User.ref == ref.name,
                User.reg_date == date,
                User.is_blocked.is_(False),
            )
        )

    formatted_dates = ["Сегодня", "Вчера"] + [
        date.strftime("%d-%m") for date in dates[2:]
    ]

    plt.figure(figsize=(12, 8), dpi=100)
    plt.plot(
        formatted_dates,
        total_counts,
        color="#1f77b4",
        marker="o",
        linestyle="-",
        linewidth=2,
        markersize=6,
        label="Общее количество пользователей",
    )
    plt.plot(
        formatted_dates,
        active_counts,
        color="#2ca02c",
        marker="s",
        linestyle="--",
        linewidth=2,
        markersize=6,
        label="Количество живых пользователей",
    )

    def add_value_labels(x, y):
        for i in range(len(x)):
            if y[i] > 0:
                plt.text(
                    i,
                    y[i],
                    format_number(y[i]),
                    ha="center",
                    va="bottom",
                    color="black",
                    fontweight="bold",
                    fontsize=8,
                    rotation=45,
                )

    add_value_labels(formatted_dates, total_counts)
    add_value_labels(formatted_dates, active_counts)

    plt.fill_between(formatted_dates, total_counts, color="#1f77b4", alpha=0.1)
    plt.fill_between(formatted_dates, active_counts, color="#2ca02c", alpha=0.1)

    plt.xlabel("Дата", fontsize=14)
    plt.ylabel("Количество пользователей", fontsize=14)
    plt.title(
        f'Статистика по ссылке {ref.name} на {today.strftime("%Y-%m-%d")}',
        fontsize=16,
        fontweight="bold",
    )

    plt.legend(loc="upper right", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45, fontsize=8)

    max_count = max(max(total_counts), max(active_counts))
    if max_count > 1000:
        plt.yscale("log")
        tick_locations = [1, 10, 100, 1000, 10000, 100000, 1000000]
        tick_locations = [loc for loc in tick_locations if loc <= max_count]
        plt.yticks(
            tick_locations, [format_number(x) for x in tick_locations], fontsize=10
        )
    else:
        plt.yticks(np.linspace(0, max_count, 6, dtype=int), fontsize=10)

    plt.tight_layout()

    image_stream = BytesIO()
    plt.savefig(image_stream, format="png", dpi=100, bbox_inches="tight")
    plt.close()
    image_stream.seek(0)

    return image_stream


def count(table, *filters):
    return select(func.count()).select_from(table).where(*filters)


def calculate_price(price, users):
    try:
        return round(price / users, 1)
    except ZeroDivisionError:
        return 0
