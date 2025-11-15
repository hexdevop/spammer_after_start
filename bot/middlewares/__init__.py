from aiogram import Dispatcher

from .callback_answer import CallbackAnswer
from .language import LanguageMiddleware
from .throttling import ThrottlingMiddleware
from .album import AlbumMiddleware


def setup(dp: Dispatcher):
    dp.update.middleware(LanguageMiddleware())

    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.callback_query.outer_middleware(ThrottlingMiddleware())

    dp.callback_query.middleware(CallbackAnswer())
