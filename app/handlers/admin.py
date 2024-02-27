from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from app.extras import helpers
from app.enums import IdleType, UserRole
from app.handlers import start
from app.filters import UserRoleFilter
from app.models import Employee, Plan
from app.keyboards import KeyboardCollection
from app.states import MainStates
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(UserRoleFilter(UserRole.ADMIN))
router.callback_query.filter(UserRoleFilter(UserRole.ADMIN))


async def main(message: Message, state: FSMContext) -> None:
    await message.answer(loc.get_text("Админка"))
