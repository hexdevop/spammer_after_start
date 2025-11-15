from typing import Dict, Any, Awaitable, Callable, Union
from aiogram import BaseMiddleware
from aiogram.types import Update


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Union[Update, Any],
        data: Dict[str, Any],
    ) -> Any:
        try:
            languages = data["languages"]
            data['lang'] = 'ru'
            data["l10n"] = languages['ru']
        except KeyError:
            pass
        return await handler(event, data)