from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.models import User
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)


@router.message()
async def service_message(message: Message) -> None:
    await message.answer(loc.get_text("bot_sleep"))


@router.callback_query()
async def service_message_callback(callback: CallbackQuery) -> None:
    await callback.message.answer(loc.get_text("bot_sleep"))
