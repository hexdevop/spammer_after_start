import asyncio
import random

import tzlocal
from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramServerError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select, update, case

from config import config
from database import get_session
from database.models import Post, User
from bot.enums import MediaType, Status


class PostManager:
    def __init__(self, bot: Bot, refresh_seconds: int = 300, interval_seconds: int | None = None):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=tzlocal.get_localzone())
        self.refresh_seconds = refresh_seconds
        self.default_interval = interval_seconds or 30
        self._posts: list[dict] = []
        self._lock = asyncio.Lock()
        self._interval_lock = asyncio.Lock()
        self._sent_buffer: dict[int, int] = {}

    def start(self):
        if not self.scheduler.get_job("refresh-posts"):
            self.scheduler.add_job(self.refresh_posts, "interval", seconds=self.refresh_seconds, id="refresh-posts", max_instances=1, coalesce=True, replace_existing=True)
        if not self.scheduler.get_job("flush-sent"):
            self.scheduler.add_job(self.flush_sent_buffer, "interval", seconds=60, id="flush-sent", max_instances=1, coalesce=True, replace_existing=True)
        self.scheduler.start(paused=False)
        asyncio.create_task(self.refresh_posts())
        asyncio.create_task(self.restore_tasks())

    async def refresh_posts(self):
        try:
            async with get_session() as session:
                posts = (await session.scalars(select(Post).where(Post.status == Status.WORKING))).all()
            prepared = []
            for p in posts:
                prepared.append(
                    {
                        "id": p.id,
                        "media_type": p.media_type,
                        "media": p.media,
                        "text": p.text,
                        "reply_markup": p.reply_markup,
                    }
                )
            async with self._lock:
                self._posts = prepared
            logger.debug(f"PostManager refreshed {len(prepared)} posts")
        except Exception as e:
            logger.exception(f"PostManager refresh failed: {e}")

    def start_user_spam(self, user_id: int, interval_seconds: int | None = None, log: bool = True):
        job_id = f"spam:{user_id}"
        interval = interval_seconds or self.default_interval
        existing = self.scheduler.get_job(job_id)
        if existing:
            existing.reschedule(trigger="interval", seconds=interval)
        else:
            self.scheduler.add_job(self._spam_tick, "interval", seconds=interval, id=job_id, args=[user_id], max_instances=1, coalesce=True, replace_existing=True)
        if log:
            logger.info(f"Started spam for user {user_id} with interval {interval}s")

    def stop_user_spam(self, user_id: int):
        job_id = f"spam:{user_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.remove_job(job_id)
            logger.info(f"Stopped spam for user {user_id}")

    async def update_all_intervals(self, new_interval: int):
        async with self._interval_lock:
            self.default_interval = new_interval
            for job in list(self.scheduler.get_jobs()):
                if job.id.startswith("spam:"):
                    job.reschedule(trigger="interval", seconds=new_interval)
            logger.info(f"Rescheduled all spam jobs to interval {new_interval}s")

    async def restore_tasks(self):
        try:
            async with get_session() as session:
                active_user_ids = (
                    await session.scalars(
                        select(User.user_id).where(User.is_blocked.is_(False), User.user_id.notin_(config.admins))
                    )
                ).all()
            restored = 0
            for user_id in active_user_ids:
                try:
                    self.start_user_spam(user_id, interval_seconds=self.default_interval, log=False)
                    restored += 1
                except Exception as e:
                    logger.warning(f"Skip invalid task record: {user_id} -> {e}")
            logger.info(f"Restored {restored} spam tasks from database")
        except Exception as e:
            logger.exception(f"Failed to restore tasks: {e}")

    async def _spam_tick(self, user_id: int):
        post = await self._get_random_post()
        if not post:
            await self.refresh_posts()
            return
        try:
            await self._send_post(user_id, post)
            await self._increment_sent(post["id"])
        except TelegramForbiddenError:
            logger.warning(f"Forbidden for user {user_id}, stopping spam")
            self.stop_user_spam(user_id)
        except TelegramBadRequest as e:
            logger.error(f"BadRequest for user {user_id}: {e}")
        except TelegramServerError as e:
            logger.error(f"ServerError for user {user_id}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in spam tick for user {user_id}: {e}")

    async def _get_random_post(self) -> dict | None:
        async with self._lock:
            if not self._posts:
                return None
            return random.choice(self._posts)

    async def _increment_sent(self, post_id: int):
        self._sent_buffer[post_id] = self._sent_buffer.get(post_id, 0) + 1

    async def flush_sent_buffer(self):
        if not self._sent_buffer:
            return
        try:
            increments = self._sent_buffer.copy()
            self._sent_buffer.clear()
            inc_case = case(
                *[(Post.id == pid, inc) for pid, inc in increments.items()],
                else_=0,
            )
            async with get_session() as session:
                async with session.begin():
                    await session.execute(
                        update(Post)
                        .where(Post.id.in_(list(increments.keys())))
                        .values(sent=Post.sent + inc_case)
                    )
        except Exception as e:
            logger.exception(f"Failed to flush sent buffer: {e}")

    def _build_reply_markup(self, data: dict | None) -> types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None:
        if not data:
            return None
        try:
            return types.InlineKeyboardMarkup.model_validate(data)
        except Exception:
            try:
                return types.ReplyKeyboardMarkup.model_validate(data)
            except Exception:
                return None

    async def _send_post(self, user_id: int, post: dict):
        markup = self._build_reply_markup(post["reply_markup"])
        text = post.get("text") or ""
        mt = post["media_type"]
        if mt is MediaType.TEXT:
            await self.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
            return
        method_name = f"send_{mt.name.lower()}"
        method = getattr(self.bot, method_name)
        key = mt.name.lower()
        params = {
            "chat_id": user_id,
            key: post["media"],
            "caption": text,
            "reply_markup": markup,
        }
        if mt in [MediaType.VIDEO_NOTE, MediaType.STICKER]:
            params.pop("caption")
        await method(**params)