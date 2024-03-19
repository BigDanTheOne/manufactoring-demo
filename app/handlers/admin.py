from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.enums import UserRole
from app.extras import helpers
from app.filters import UserRoleFilter
from app.keyboards import KeyboardCollection
from app.models import Account, Operator, ProductionLine
from app.states import AdminStates
from loaders import loc

router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(UserRoleFilter(UserRole.ADMIN))
router.callback_query.filter(UserRoleFilter(UserRole.ADMIN))


async def main(obj: Message | CallbackQuery, state: FSMContext) -> None:
    if isinstance(obj, CallbackQuery):
        await helpers.hide_markup_or_delete(obj)
    if (message := helpers.resolve_message(obj)) is None:
        return

    await state.set_state(AdminStates.main)
    await message.answer(
        loc.get_text("admin/choose_action"), reply_markup=KeyboardCollection().admin_keyboard()
    )


@router.callback_query(F.data == "add_operator", AdminStates.main)
async def handle_add_operator_btn(callback: CallbackQuery, state: FSMContext) -> None:
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return
    await state.set_state(AdminStates.add_operator)
    await message.answer(loc.get_text("admin/operator/name"))


@router.message(F.text, AdminStates.add_operator)
async def handle_name_input(message: Message, state: FSMContext) -> None:
    await state.update_data(operator_name=message.text)
    await state.set_state(AdminStates.operator_rate)

    await message.answer(loc.get_text("admin/operator/rate"))


@router.message(F.text, AdminStates.operator_rate)
async def handle_rate_input(message: Message, state: FSMContext) -> None:
    if not helpers.is_int(message.text) and not helpers.is_float(message.text):
        await message.answer(loc.get_text("admin/operator/wrong_input"))
        return

    if helpers.is_int(message.text):
        rate = int(message.text)
    elif helpers.is_float(message.text):
        rate = float(message.text)
    else:
        return

    await state.set_state(AdminStates.operator_line)
    await state.update_data(operator_rate=rate)
    lines = await ProductionLine.all().to_list()
    await message.answer(
        loc.get_text("admin/operator/choose_line"),
        reply_markup=KeyboardCollection().choose_line_keyboard(lines),
    )


@router.callback_query(F.data.startswith("line"), AdminStates.operator_line)
async def handle_line_btn(callback: CallbackQuery, state: FSMContext) -> None:
    line_id = callback.data.split(":")[1]
    if (line := await ProductionLine.get(line_id)) is None:
        return
    storage_data = await state.get_data()
    if (operator_name := storage_data.get("operator_name")) is None:
        return
    if (operator_rate := storage_data.get("operator_rate")) is None:
        return

    new_operator = Operator(
        name=operator_name,
        rate=operator_rate,
        line_id=line.id,
        progress_log=[],
    )
    await new_operator.insert()

    await callback.answer(loc.get_text("admin/operator/added"))
    await main(callback, state)


@router.callback_query(F.data == "add_account", AdminStates.main)
async def handle_add_account_btn(callback: CallbackQuery, state: FSMContext) -> None:
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return
    await state.set_state(AdminStates.add_account)
    await message.answer(loc.get_text("admin/account/phone"))


@router.message(F.text, AdminStates.add_account)
async def handle_phone_input(message: Message, state: FSMContext) -> None:
    phone = helpers.get_pure_phone(message.text)

    new_account = Account(phone=phone, role=UserRole.OPERATOR)
    await new_account.insert()

    await message.answer(loc.get_text("admin/account/added"))
    await main(message, state)
