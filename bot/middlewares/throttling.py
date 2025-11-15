from __future__ import annotations
from typing import *
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
import time
from collections import defaultdict

from config import config


def rate_limit(limit: int, key=None):
    def decorator(func):
        setattr(func, "throttling_rate_limit", limit)
        if key:
            setattr(func, "throttling_key", key)
        return func

    return decorator


class MemoryStorage:
    def __init__(self):
        self.storage = defaultdict(dict)

    def get(self, key):
        return self.storage.get(key, {})

    def set(self, key, value):
        self.storage[key] = value


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=0.5, key_prefix="antiflood_"):
        self.rate_limit = limit
        self.prefix = key_prefix
        self.throttle_manager = ThrottleManager()
        super(ThrottlingMiddleware, self).__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        try:
            await self.on_process_event(event, data)
        except CancelHandler:
            return
        return await handler(event, data)

    async def on_process_event(
        self,
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        limit = getattr(
            data["handler"].callback, "throttling_rate_limit", self.rate_limit
        )
        key = getattr(
            data["handler"].callback, "throttling_key", f"{self.prefix}_message"
        )

        chat = data.get("event_chat")
        user = data.get("event_from_user")
        if user.id not in config.admins:
            try:
                await self.throttle_manager.throttle(
                    key, rate=limit, user_id=user.id, chat_id=chat.id
                )
            except Throttled as t:
                await self.event_throttled(event, t)
                raise CancelHandler()

    @staticmethod
    async def event_throttled(event: Message, throttled: Throttled):
        delta = throttled.rate - throttled.delta
        if throttled.exceeded_count <= 2:
            try:
                await event.answer(
                    f"Слишком много запросов. Попробуйте снова через {delta:.2f} секунд."
                )
            except TelegramBadRequest:
                pass


class ThrottleManager:
    def __init__(self):
        self.storage = MemoryStorage()

    async def throttle(self, key: str, rate: float, user_id: int, chat_id: int):
        now = time.time()
        bucket_name = f"throttle_{key}_{user_id}_{chat_id}"

        data = self.storage.get(bucket_name)
        if not data:
            data = {
                "RATE_LIMIT": rate,
                "LAST_CALL": now,
                "DELTA": 0,
                "EXCEEDED_COUNT": 1,
            }
        else:
            called = data["LAST_CALL"]
            delta = now - called
            result = delta >= rate or delta <= 0

            data["RATE_LIMIT"] = rate
            data["LAST_CALL"] = now
            data["DELTA"] = delta
            if not result:
                data["EXCEEDED_COUNT"] += 1
            else:
                data["EXCEEDED_COUNT"] = 1

            if not result:
                self.storage.set(bucket_name, data)
                raise Throttled(key=key, chat=chat_id, user=user_id, **data)

        self.storage.set(bucket_name, data)
        return True


class Throttled(Exception):
    def __init__(self, **kwargs):
        self.key = kwargs.pop("key", "<None>")
        self.called_at = kwargs.pop("LAST_CALL", time.time())
        self.rate = kwargs.pop("RATE_LIMIT", None)
        self.exceeded_count = kwargs.pop("EXCEEDED_COUNT", 0)
        self.delta = kwargs.pop("DELTA", 0)
        self.user = kwargs.pop("user", None)
        self.chat = kwargs.pop("chat", None)

    def __str__(self):
        return (
            f"Превышен лимит запросов! (Лимит: {self.rate} с, "
            f"превышено: {self.exceeded_count}, "
            f"временная дельта: {round(self.delta, 3)} с)"
        )


class CancelHandler(Exception):
    pass
