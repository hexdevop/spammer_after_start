from aiogram import Dispatcher

from . import (
    admin,
    user,
    other,
)


def setup(dp: Dispatcher):
    admin.reg_routers(dp)
    user.reg_packages(dp)
    other.reg_routers(dp)
