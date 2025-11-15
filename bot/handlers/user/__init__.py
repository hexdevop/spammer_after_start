from aiogram import Dispatcher

from . import (
    default,
    deep_link,
    main,
)


def reg_packages(dp: Dispatcher):
    packages = [
        default,
        deep_link,
        main,

    ]
    for package in packages:
        package.reg_routers(dp)
