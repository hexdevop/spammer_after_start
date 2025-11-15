from aiogram.utils.keyboard import ReplyKeyboardBuilder
from fluent.runtime import FluentLocalization


def main_menu(l10n: FluentLocalization, is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.button(text=l10n.format_value("button"))
    sub_size = 0
    if is_admin:
        builder.button(text="Панель администратора ⚙️")
        sub_size += 1
    return builder.adjust(1, sub_size).as_markup(
        resize_keyboard=True, input_field_placeholder="Главное меню 💠"
    )
