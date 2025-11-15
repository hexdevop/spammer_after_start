from aiogram.filters import BaseFilter

from config import config


class AdminFilter(BaseFilter):
    async def __call__(self, event) -> bool:
        return event.from_user.id in config.admins
