from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram_widgets.pagination import KeyboardPaginator

from app import utils
from app.extras import helpers
from app.filters import UserRoleFilter
from app.models import User, Employee, Plan
from app.enums import UserRole
from app.keyboards import KeyboardCollection
from app.states import MainStates
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
    if await User.by_tg_id(message.chat.id) is None:
        await state.set_state(MainStates.contact_confirm)
        await message.answer(
            loc.get_text(
                "Отправьте номер телефона, чтобы активировать Оператора."
            ),
            reply_markup=kbc.contact_keyboard(),
        )
        return
    await choose_employee(message, state)


@router.message(F.contact, MainStates.contact_confirm)
async def handle_contact(message: Message, state: FSMContext) -> None:
    phone = helpers.get_pure_phone(message.contact.phone_number)
    if (user := await User.by_phone(phone)) is None:
        await message.answer(
            loc.get_text("Оператор не найден. Обратитесь к администратору."),
        )
        return
    user.tg_id = message.from_user.id
    await user.save()
    await choose_employee(message, state)


async def choose_employee(message: Message, state: FSMContext) -> None:
    kbc = KeyboardCollection()
    employee_buttons = await kbc.employee_buttons()
    paginator = KeyboardPaginator(
        data=employee_buttons,
        router=router,
        per_page=10,
        per_row=2,
    )
    await state.set_state(MainStates.choose_employee)
    await message.answer(
        loc.get_text("Выберите оператора"), reply_markup=paginator.as_markup()
    )


@router.callback_query(
    F.data.startswith("employee"), MainStates.choose_employee
)
async def handle_chosen_employee(
    callback: CallbackQuery, state: FSMContext
) -> None:
    employee_id = callback.data.split(":")[1]
    await state.update_data(employee_id=employee_id)

    if (employee := await Employee.get(employee_id)) is None:
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.choose_action)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(employee.name),
        reply_markup=kbc.choose_action_keyboard(),
    )
