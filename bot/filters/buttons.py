from typing import Union

from aiogram import types
from aiogram.filters import BaseFilter
from fluent.runtime import FluentLocalization


class Button(BaseFilter):
    def __init__(self, btn: Union[str, list]):
        self.btn = btn

    async def __call__(self, message: types.Message, l10n: FluentLocalization) -> bool:
        if message.text:
            if isinstance(self.btn, str):
                return message.text == l10n.format_value(self.btn)
            else:
                return message.text in [l10n.format_value(i) for i in self.btn]
