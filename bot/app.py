import tzlocal
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.services import PostManager
from bot.utils import fluent_loader
from config import config

bot = Bot(
    token=config.bot.token,
    session=AiohttpSession(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML, protect_content=False, link_preview_is_disabled=True
    ),
)

storage = MemoryStorage()

scheduler = AsyncIOScheduler(timezone=tzlocal.get_localzone())

languages = fluent_loader.get_fluent_localization()

post_manager = PostManager(bot=bot, refresh_seconds=300, interval_seconds=config.interval)

dp = Dispatcher(
    storage=storage,
    scheduler=scheduler,
    languages=languages,
    config=config,
    post_manager=post_manager,
)