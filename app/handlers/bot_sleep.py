from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.models import User
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)


@router.message()
async def service_message(message: Message) -> None:
    user = await User.by_tg_id(message.chat.id)
    if user:
        text = loc.get_text("bot_sleep", user.language)
    else:
        bot_sleep_ru = loc.get_text("bot_sleep", "ru")
        bot_sleep_en = loc.get_text("bot_sleep", "en")
        text = f"{bot_sleep_ru}\n\n{bot_sleep_en}"
    await message.answer(text)


@router.callback_query()
async def service_message_callback(callback: CallbackQuery) -> None:
    user = await User.by_tg_id(callback.message.chat.id)
    if user:
        text = loc.get_text("bot_sleep", user.language)
    else:
        bot_sleep_ru = loc.get_text("bot_sleep", "ru")
        bot_sleep_en = loc.get_text("bot_sleep", "en")
        text = f"{bot_sleep_ru}\n\n{bot_sleep_en}"
    await callback.message.answer(text)
