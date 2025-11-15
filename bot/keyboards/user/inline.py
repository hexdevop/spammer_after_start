from typing import List

from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluent.runtime import FluentLocalization

from database.models import Subscription


def subscription(l10n: FluentLocalization, subscriptions: List[Subscription]):
    builder = InlineKeyboardBuilder()
    for i in subscriptions:
        builder.button(
            text=f"{i.type.value} | {i.title}",
            url=i.url,
        )
    builder.button(text=l10n.format_value('im-subscribed'), callback_data="check-subscriptions")
    return builder.adjust(
        *[*[2 for _ in range(len(subscriptions) // 2)], 1]
    ).as_markup()
