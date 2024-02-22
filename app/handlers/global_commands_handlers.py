from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext

from app import utils
from app.handlers import main_menu_handlers
from app.handlers.company import company_register_handlers
from app.filters import UserRoleFilter
from app.models import User, Company
from app.enums import UserRole
from app.keyboards import KeyboardCollection
from app.states import RegisterStates
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)


@router.message(CommandStart(deep_link=True))
async def start_cmd_deep_linked(
    message: Message, state: FSMContext, command: CommandObject
) -> None:
    args = command.args

    if not args:
        await state.clear()

    user = await User.by_tg_id(message.chat.id)
    if user is None:
        if args:
            if args.startswith("join_company-"):
                company_id = args.replace("join_company-", "")
                # пока только для `Х10 Движение`, потом можно будет убрать это условие
                if company_id == "65114d7a43b93a79f974e516":
                    await state.update_data(deep_linked_company_id=company_id)
            else:
                await state.update_data(referral_id=args)

        await state.set_state(RegisterStates.setup_language)

        kbc = KeyboardCollection("ru")
        await message.answer(
            "Выберите язык / Choose language:",
            reply_markup=kbc.language_keyboard(),
        )
        return
    if args and args.startswith("register_company_"):
        company_id = args.replace("register_company_", "")
        await state.update_data(company_id=company_id)
        await company_register_handlers.entry_point(message, state, user)
        return

    # если юзер зареган и вступает в компанию
    if args and args.startswith("join_company-"):
        company_id = args.replace("join_company-", "")
        # пока только для `Х10 Движение`, потом можно будет убрать это условие
        if company_id == "65114d7a43b93a79f974e516":
            await join_company(message, company_id)
            return

    await main_menu_handlers.entry_point(message, state, user)


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await User.by_tg_id(message.chat.id)
    if user is None:
        await state.set_state(RegisterStates.setup_language)
        kbc = KeyboardCollection("ru")
        await message.answer(
            "Выберите язык / Choose language:",
            reply_markup=kbc.language_keyboard(),
        )
        return
    await main_menu_handlers.entry_point(message, state, user)


@router.message(Command("menu"))
async def handle_menu_command(message: Message, state: FSMContext) -> None:
    if (user := await User.by_tg_id(message.chat.id)) is None:
        return
    await main_menu_handlers.entry_point(message, state, user)


@router.message(Command("ping"))
async def ping_cmd(message: Message) -> None:
    await message.answer("pong")


@router.message(Command("dump"), UserRoleFilter(UserRole.ADMIN))
async def dump_cmd(message: Message) -> None:
    utils.make_db_dump()
    zip_file = utils.zip_folder("../storage/dump")
    await utils.send_dump([message.from_user.id], zip_file)


async def join_company(message: Message, company_id: str) -> None:
    if (company := await Company.get(company_id)) is None:
        return
    if user := await User.by_tg_id(message.from_user.id):
        if await user.as_employee_of(company.id) is None:
            await company.add_employee(user.id)
            await message.answer(
                loc.get_text("company/x10/joined", user.language)
            )
        else:
            await message.answer(
                loc.get_text("company/x10/already_joined", user.language)
            )
