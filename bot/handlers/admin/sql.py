from aiogram import types, Router
from aiogram.filters import Command, CommandObject
from sqlalchemy import text

from database import get_session
from tabulate import tabulate

router = Router()


@router.message(Command("sql"))
async def sql_command(
    message: types.Message,
    command: CommandObject,
):
    if not command.args:
        await message.reply(
            "Пожалуйста, укажите SQL-запрос. Пример: /sql SELECT * FROM users;"
        )
        return

    query = command.args

    try:
        async with get_session() as session:
            async with session.begin():
                result = await session.execute(text(query))

                affected_rows = result.rowcount

                if query.strip().lower().startswith(
                    "select"
                ) or query.strip().lower().startswith("show"):
                    rows = result.fetchall()
                    if rows:
                        headers = result.keys()
                        response = tabulate(rows, headers=headers, tablefmt="pretty")
                    else:
                        response = "Результатов нет."
                else:
                    await session.commit()
                    response = "Запрос выполнен успешно."

        response += f"\n\nЗатронуто записей: {affected_rows}"

        await message.reply(f"```\n{response}\n```", parse_mode="Markdown")

    except Exception as e:
        # Обработка ошибок
        await message.reply(f"Ошибка при выполнении запроса: {e}")
