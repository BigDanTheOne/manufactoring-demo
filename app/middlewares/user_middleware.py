import asyncio
from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from app.models import User
from loaders import loc


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [Message | CallbackQuery, dict[str, Any]], Awaitable[Any]
        ],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            chat_id = event.chat.id
        if isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id

        user = await User.by_tg_id(chat_id)
        if user is None:
            return await handler(event, data)
        if user.banned and isinstance(event, Message):
            await event.answer(loc.get_text("main_menu/banned", user.language))
            return
        elif user.banned and isinstance(event, CallbackQuery):
            await event.message.answer(
                loc.get_text("main_menu/banned", user.language)
            )
            return
        user.tg_username = event.from_user.username
        await user.save()

        data["user"] = user
        return await handler(event, data)
