from aiogram.fsm.state import StatesGroup, State


class RefState(StatesGroup):
    name = State()
    price = State()


class SpamState(StatesGroup):
    post = State()
    interval = State()
