from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from app import utils
from app.extras import helpers
from app.filters import UserRoleFilter
from app.handlers import operator, admin
from app.models import Account
from app.enums import UserRole
from app.keyboards import KeyboardCollection
from app.states import AccountStates
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)


@router.message(Command("ping"))
async def ping_cmd(message: Message) -> None:
    await message.answer("pong")


@router.message(Command("dump"), UserRoleFilter(UserRole.ADMIN))
async def dump_cmd(message: Message) -> None:
    utils.make_db_dump()
    zip_file = utils.zip_folder("../storage/dump")
    await utils.send_dump([message.from_user.id], zip_file)


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    kbc = KeyboardCollection()
    if (user := await Account.by_tg_id(message.chat.id)) is None:
        await state.set_state(AccountStates.contact_confirm)
        await message.answer(
            loc.get_text("start/send_contact"),
            reply_markup=kbc.contact_keyboard(),
        )
        return

    if user.role == UserRole.OPERATOR:
        await operator.choose_line(message, state)
    elif user.role == UserRole.ADMIN:
        await admin.main(message, state)
    else:
        return


@router.message(F.contact, AccountStates.contact_confirm)
async def handle_contact(message: Message, state: FSMContext) -> None:
    phone = helpers.get_pure_phone(message.contact.phone_number)
    if (user := await Account.by_phone(phone)) is None:
        await message.answer(
            loc.get_text("start/user_not_found"),
        )
        return

    await message.answer(
        loc.get_text("Аккаунт активирован"), reply_markup=ReplyKeyboardRemove()
    )

    user.tg_id = message.from_user.id
    await user.save()

    if user.role == UserRole.OPERATOR:
        await operator.choose_line(message, state)
    elif user.role == UserRole.ADMIN:
        await admin.main(message, state)
    else:
        return
