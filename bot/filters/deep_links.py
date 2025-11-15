from typing import Union, Dict, Any

from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from aiogram import Bot


class DeepLink(CommandStart):
    def __init__(self, prefix: str):
        super().__init__(deep_link=True, deep_link_encoded=True)
        self.__prefix = prefix

    async def __call__(self, message: Message, bot: Bot) -> Union[bool, Dict[str, Any]]:
        response = await super().__call__(message, bot)
        if response:
            command: CommandObject = response.get("command")
            if command.args.startswith(self.__prefix):
                return {"command": command}
        return False
