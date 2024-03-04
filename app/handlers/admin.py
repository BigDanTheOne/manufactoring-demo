from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from app.extras import helpers
from app.enums import IdleType, UserRole
from app.handlers import start
from app.filters import UserRoleFilter
from app.models import Operator, Account
from app.keyboards import KeyboardCollection
from app.states import AdminStates
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(UserRoleFilter(UserRole.ADMIN))
router.callback_query.filter(UserRoleFilter(UserRole.ADMIN))


async def main(message: Message, state: FSMContext) -> None:
    await helpers.try_delete_message(message)
    await state.set_state(AdminStates.main)

    kbc = KeyboardCollection()
    await message.answer(
        loc.get_text("Выберите действие"), reply_markup=kbc.admin_keyboard()
    )


@router.callback_query(F.data == "add_operator", AdminStates.main)
async def handle_add_operator_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(AdminStates.add_operator)
    await callback.message.answer(loc.get_text("Введите ФИО оператора:"))


@router.message(F.text, AdminStates.add_operator)
async def handle_name_input(message: Message, state: FSMContext) -> None:
    await state.update_data(operator_name=message.text)
    await state.set_state(AdminStates.operator_rate)

    await message.answer(loc.get_text("Введите ставку оператора:"))


@router.message(F.text, AdminStates.operator_rate)
async def handle_rate_input(message: Message, state: FSMContext) -> None:
    if not helpers.is_int(message.text) and not helpers.is_float(message.text):
        await message.answer(loc.get_text("Нужно ввести число"))
        return

    storage_data = await state.get_data()
    if (operator_name := storage_data.get("operator_name")) is None:
        return

    rate: int | float
    if helpers.is_int(message.text):
        rate = int(message.text)
    elif helpers.is_float(message.text):
        rate = float(message.text)
    else:
        return

    new_operator = Operator(name=operator_name, rate=rate)
    await new_operator.insert()

    await message.answer(loc.get_text("Сотрудник добавлен"))
    await main(message, state)


@router.callback_query(F.data == "add_account", AdminStates.main)
async def handle_add_account_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(AdminStates.add_account)
    await callback.message.answer(
        loc.get_text("Введите номер телефона аккаунта:")
    )


@router.message(F.text, AdminStates.add_account)
async def handle_phone_input(message: Message, state: FSMContext) -> None:
    phone = helpers.get_pure_phone(message.text)

    new_account = Account(phone=phone, role=UserRole.OPERATOR)
    await new_account.insert()

    await message.answer(loc.get_text("Аккаунт создан"))
    await main(message, state)
