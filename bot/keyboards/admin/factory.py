from aiogram.filters.callback_data import CallbackData


class LoadOutCallbackData(CallbackData, prefix="l"):
    action: str


class RefCallbackData(CallbackData, prefix="r"):
    action: str
    page: int

    id: int = 0


class ErrorsCallbackData(CallbackData, prefix="err"):
    id: int
    location: str
    action: str
    page: int


class SpamCallbackData(CallbackData, prefix="sp"):
    action: str
    page: int

    id: int = 0