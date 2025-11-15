from math import ceil

from config import config
from database.models import Ref, Post
from bot.keyboards.admin.factory import (
    LoadOutCallbackData,
    RefCallbackData,
    ErrorsCallbackData, SpamCallbackData,
)
from bot.keyboards.utils import *


# LOAD OUT


def load_out(buttons: dict, selected: dict):
    builder = InlineKeyboardBuilder()

    def order_button(button_text: str, data: LoadOutCallbackData):
        builder.button(
            text=button_text + (" 🟢" if data.action == selected.get("order") else ""),
            callback_data=data.pack(),
        )

    for action, text in buttons.get("order").items():
        order_button(text, LoadOutCallbackData(action=action))

    builder.button(
        text="Выгрузить ⤵️",
        callback_data=LoadOutCallbackData(
            action="start",
        ).pack(),
    )
    return builder.adjust(3).as_markup()


# REFS


def refs_list(
    refs: List[Ref],
    width: int = 3,
    height: int = 8,
    page: int = 1,
):
    builder = InlineKeyboardBuilder()
    s = width * height
    length = ceil(len(refs) / s)
    data = RefCallbackData(
        action="settings",
        page=page,
    )
    for ref in refs[s * (page - 1) : s * page]:
        data.id = ref.id
        builder.button(text=f"{ref.name} | {ref.follows}", callback_data=data.pack())
    sizes = []
    sizes = generate_sizes(sizes, refs, width, height, page)
    return with_pagination(builder, data, length, page, sizes)


def referral_settings(data: RefCallbackData):
    builder = InlineKeyboardBuilder()
    data.action = "price"
    builder.button(text="Задать/Изменить цену 💵", callback_data=data.pack())
    data.action = "graph"
    builder.button(text="График 📈", callback_data=data.pack())
    data.action = "delete"
    builder.button(text="Удалить 🗑", callback_data=data.pack())
    data.action = "main"
    builder.button(text="🔙 Назад", callback_data=data.pack())
    return builder.adjust(1).as_markup()


def errors_list(errors: List, width: int = 1, height: int = 10, page: int = 1):
    builder = InlineKeyboardBuilder()
    size = width * height
    length = ceil(len(errors) / size) or 1
    data = ErrorsCallbackData(id=0, action="status", location="n", page=page)
    builder.button(
        text="🔔 Уведомления | %s" % ("🟢" if config.error_notification else "🔴"),
        callback_data=data.pack()
    )
    sizes = [1]
    for code, location, count, latest_id in errors:
        data.id = latest_id
        data.location = location
        data.action = 'error'
        builder.button(
            text=f'{code} • {count}',
            callback_data=data.pack(),
        )
        data.action = 'fixed'
        builder.button(
            text='Исправлена ✅',
            callback_data=data.pack(),
        )
        sizes.append(2)
    return with_pagination(builder, data, length, page, sizes)


def spam_list(
    posts: List[Post],
    width: int = 2,
    height: int = 8,
    page: int = 1,
):
    builder = InlineKeyboardBuilder()
    s = width * height
    length = ceil(len(posts) / s)
    data = SpamCallbackData(
        action="interval",
        page=page,
    )
    builder.button(
        text=f'🕓 Интервал | {config.interval}',
        callback_data=data.pack()
    )
    sizes = [1]
    for show in posts:
        data.action = 'settings'
        data.id = show.id
        builder.button(
            text=f"#{show.id} | {show.media_type.value}", callback_data=data.pack()
        )
    sizes = generate_sizes(sizes, posts, width, height, page)
    builder, size = with_pagination(builder, data, length, page, sizes, as_markup=False)
    data.action = "add"
    builder.button(text="➕", callback_data=data.pack())
    sizes.append(1)
    return builder.adjust(*sizes).as_markup()


def spam_settings(
    data: SpamCallbackData,
):
    builder = InlineKeyboardBuilder()
    data.action = "check-post"
    builder.button(text="👀 Посмотреть полный пост", callback_data=data.pack())
    data.action = "change-status"
    builder.button(text="🛠 Сменить статус", callback_data=data.pack())
    data.action = "delete"
    builder.button(text="🗑 Удалить", callback_data=data.pack())
    data.action = "main"
    builder.button(text="🔙 Назад", callback_data=data.pack())
    return builder.adjust(1).as_markup()
