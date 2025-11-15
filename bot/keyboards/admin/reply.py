from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_admin():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Статистика 📊")
    builder.button(text="Выгрузка 🗳")
    builder.button(text="Спам 💬")
    builder.button(text="Рефералы 💵")
    builder.button(text="🔙 Панель подписчиков")
    return builder.adjust(1, 3, 1).as_markup(
        resize_keyboard=True, input_field_placeholder="Админ панель 🏚"
    )


def referral_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Создать реф. ссылку 🆕")
    builder.button(text="Список реф. ссылок 📋")
    builder.button(text="🔙 Назад в админ панель 🏚")
    return builder.adjust(1).as_markup(
        resize_keyboard=True, input_field_placeholder="Меню рефок 💵"
    )


def generate_new_ref():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Сгенерировать ✍️")
    builder.button(text="🚫 Отмена")
    return builder.adjust(1).as_markup(
        resize_keyboard=True, input_field_placeholder="«🚫 Отмена» чтобы вернутся"
    )


def skip_and_cancel():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пропустить ⏭")
    builder.button(text="🚫 Отмена")
    return builder.adjust(1).as_markup(
        resize_keyboard=True, input_field_placeholder="«🚫 Отмена» чтобы вернутся"
    )

