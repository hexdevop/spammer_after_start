import datetime
from io import BytesIO
import numpy as np

import matplotlib.pyplot as plt
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database import get_session
from database.models import User
from bot.utils import helper


router = Router()


def count(table, *filters):
    return select(func.count()).select_from(table).where(*filters)


@router.message(F.text == "Статистика 📊")
async def statistic(
    message: types.Message,
    state: FSMContext,
    l10n: FluentLocalization,
):
    await state.clear()
    async with get_session() as session:
        # users
        total = await session.scalar(count(User))
        active = await session.scalar(count(User, User.is_blocked.is_(False)))
        self_growth = await session.scalar(count(User, User.ref.is_(None)))

        day = datetime.date.today()

        today = await session.scalar(count(User, User.reg_date >= day))
        week = await session.scalar(
            count(User, User.reg_date >= day - datetime.timedelta(days=6))
        )
        month = await session.scalar(
            count(User, User.reg_date >= day - datetime.timedelta(days=30))
        )

        top_5_langs = (
            await session.scalars(
                select(User.lang_code)
                .group_by(User.lang_code)
                .order_by(func.count().desc())
                .limit(5)
            )
        ).all()
        langs_text = ""
        for i, item in enumerate(top_5_langs, start=1):
            lang_count = await session.scalar(count(User, User.lang_code == item))
            langs_text += (
                f"{i}. {item.upper()}"
                f"    <code>{lang_count}</>"
                f"    <code>({helper.get_percent(total, lang_count)}%)</>\n"
            )
            if len(top_5_langs) == i:
                lang_count = await session.scalar(
                    count(User, User.lang_code.notin_(top_5_langs))
                )
                langs_text += (
                    f"{i + 1}. Остальные"
                    f"    <code>{lang_count}</>"
                    f"    <code>({helper.get_percent(total, lang_count)}%)</>\n"
                )

        params = {
            "total": total,
            "self": self_growth,
            "self_percent": helper.get_percent(total, self_growth),
            "active": active,
            "active_percent": helper.get_percent(total, active),
            "death": total - active,
            "death_percent": helper.get_percent(total, total - active),
            "today": today,
            "week": week,
            "month": month,
            "langs": langs_text,
        }
        text = l10n.format_value("statistic", params)
        msg = await message.answer_animation(
            "https://c.tenor.com/jfmI0j5FcpAAAAAd/tenor.gif", caption=text
        )
        image_stream = await generate_statistic_graph(session)
        await msg.edit_media(
            media=types.InputMediaPhoto(
                media=types.BufferedInputFile(
                    image_stream.getvalue(), filename="graph.jpg"
                ),
                caption=text,
            )
        )


def format_number(num):
    if num >= 1000000:
        return f"{num / 1000000:.1f}М"
    elif num >= 1000:
        return f"{num / 1000:.1f}к"
    else:
        return str(num)


async def generate_statistic_graph(
    session: AsyncSession,
):
    today = datetime.datetime.now().date()  # Используем только дату, без времени
    start_date = today - datetime.timedelta(
        days=29
    )  # Последние 30 дней включая сегодня

    new_users_query = (
        await session.execute(
            select(
                func.date(User.reg_date).label("date"),
                func.count(User.id).label("new_users"),
            )
            .where(User.reg_date >= start_date)
            .group_by(func.date(User.reg_date))
        )
    ).fetchall()

    blocked_users_query = (
        await session.execute(
            select(
                func.date(User.death_date).label("date"),
                func.count(User.id).label("blocked_users"),
            )
            .where(
                and_(User.death_date >= start_date, User.is_blocked.is_(True))
            )
            .group_by(func.date(User.death_date))
        )
    ).fetchall()

    organic_users_query = (
        await session.execute(
            select(
                func.date(User.reg_date).label("date"),
                func.count(User.id).label("organic_users"),
            )
            .where(and_(User.reg_date >= start_date, User.ref.is_(None)))
            .group_by(func.date(User.reg_date))
        )
    ).fetchall()

    dates = [
        start_date + datetime.timedelta(days=i) for i in range(30)
    ]  # Список дат от начальной до сегодняшней
    formatted_dates = [
        (
            "Сегодня"
            if date == today
            else (
                "Вчера"
                if date == today - datetime.timedelta(days=1)
                else date.strftime("%d-%m")
            )
        )
        for date in dates
    ]

    new_users = {date: 0 for date in dates}
    blocked_users = {date: 0 for date in dates}
    organic_users = {date: 0 for date in dates}

    for record in new_users_query:
        new_users[record.date] = record.new_users
    for record in blocked_users_query:
        blocked_users[record.date] = record.blocked_users
    for record in organic_users_query:
        organic_users[record.date] = record.organic_users

    y1 = [new_users[date] for date in dates]
    y2 = [blocked_users[date] for date in dates]
    y3 = [organic_users[date] for date in dates]

    plt.figure(figsize=(12, 8), dpi=100)

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

    plt.plot(
        formatted_dates,
        y1,
        color="#1f77b4",
        marker="o",
        linestyle="-",
        linewidth=2,
        markersize=6,
        label="Общий приход подписчиков",
    )
    add_value_labels(formatted_dates, y1)

    plt.plot(
        formatted_dates,
        y2,
        color="#d62728",
        marker="s",
        linestyle="--",
        linewidth=2,
        markersize=6,
        label="Количество блоков в день",
    )
    add_value_labels(formatted_dates, y2)

    plt.plot(
        formatted_dates,
        y3,
        color="#ffbf00",
        marker="^",
        linestyle="-.",
        linewidth=2,
        markersize=6,
        label="Саморост",
    )
    add_value_labels(formatted_dates, y3)

    plt.fill_between(formatted_dates, y1, color="#1f77b4", alpha=0.1)
    plt.fill_between(formatted_dates, y2, color="#d62728", alpha=0.1)
    plt.fill_between(formatted_dates, y3, color="#ffbf00", alpha=0.1)

    plt.xlabel("Дата", fontsize=14)
    plt.ylabel("Количество пользователей", fontsize=14)
    plt.title(
        f'Статистика @{config.bot.username} за {today.strftime("%d-%m-%Y")}',
        fontsize=16,
        fontweight="bold",
    )
    plt.legend(loc="upper left", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45, fontsize=8)

    max_count = max(max(y1), max(y2), max(y3))
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
