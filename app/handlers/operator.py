from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram_widgets.pagination import KeyboardPaginator

from app.extras import helpers
from app.enums import IdleType, UserRole
from app.filters import UserRoleFilter
from app.models import Employee, Plan
from app.keyboards import KeyboardCollection
from app.states import MainStates
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(UserRoleFilter(UserRole.OPERATOR))
router.callback_query.filter(UserRoleFilter(UserRole.OPERATOR))


async def choose_line(message: Message, state: FSMContext) -> None:
    kbc = KeyboardCollection()
    await state.set_state(MainStates.choose_line)
    await message.answer(
        loc.get_text("Выберите линию"), reply_markup=kbc.choose_line_keyboard()
    )


@router.callback_query(F.data.startswith("line"), MainStates.choose_line)
async def handle_chosen_line(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (line_name := storage_data.get("line_name")) is None:
        line_name = callback.data.split(":")[1]
    await state.update_data(line_name=line_name)

    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.choose_employee)

    kbc = KeyboardCollection()
    employee_buttons = await kbc.employee_buttons()
    paginator = KeyboardPaginator(
        data=employee_buttons,
        router=router,
        per_page=10,
        per_row=2,
    )

    await callback.message.answer(
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


@router.callback_query(F.data == "start_shift", MainStates.choose_action)
async def handle_start_shift_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await state.update_data(order_id=None)
    await state.update_data(bundle_id=None)

    storage_data = await state.get_data()
    if (employee_id := storage_data.get("employee_id")) is None:
        return
    if (employee := await Employee.get(employee_id)) is None:
        return

    plan = Plan.get_plan()

    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.choose_order)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(f"{employee.name}\n\nВыберите заказ"),
        reply_markup=kbc.choose_order_keyboard(orders=plan.orders),
    )


@router.callback_query(F.data.startswith("order"), MainStates.choose_order)
async def handle_chosen_order(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (order_id := storage_data.get("order_id")) is None:
        order_id = callback.data.split(":")[1]
    await state.update_data(order_id=order_id)

    plan = Plan.get_plan()
    order = plan.get_order(order_id)

    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.choose_bundle)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(
            "<b>{}</b>\n\nЛиния: {}\nОбщая масса: {}\nОбщая длина: {}\nВремя выполнения: {}\n\nВыберите изготавливаемую пачку:".format(
                order.name,
                order.production_line_id,
                order.total_mass,
                order.total_length,
                order.execution_time,
            )
        ),
        reply_markup=kbc.choose_bundle_keyboard(order.bundles),
    )


@router.callback_query(F.data.startswith("bundle"), MainStates.choose_bundle)
async def handle_chosen_bundle(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (bundle_id := storage_data.get("bundle_id")) is None:
        bundle_id = callback.data.split(":")[1]
    await state.update_data(bundle_id=bundle_id)
    if (order_id := storage_data.get("order_id")) is None:
        return

    plan = Plan.get_plan()
    order = plan.get_order(order_id)
    bundle = order.get_bundle(bundle_id)

    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.choose_product)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(
            "<b>{}</b>\n\nОбщая масса: {}\nОбщая длина: {}\nВремя выполнения: {}\n\nВыберите изделие:.".format(
                bundle.id,
                bundle.total_mass,
                bundle.total_length,
                bundle.execution_time,
            )
        ),
        reply_markup=kbc.choose_product_keyboard(bundle.products),
    )


@router.callback_query(F.data.startswith("product"), MainStates.choose_product)
async def handle_chosen_product(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        product_id = callback.data.split(":")[1]
    await state.update_data(product_id=product_id)

    if (order_id := storage_data.get("order_id")) is None:
        return
    if (bundle_id := storage_data.get("bundle_id")) is None:
        return

    plan = Plan.get_plan()
    order = plan.get_order(order_id)
    bundle = order.get_bundle(bundle_id)
    product = bundle.get_product(product_id)

    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.enter_result)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(
            "<b>{}</b>\n\nПрофиль: {}\nШирина: {}\nТолщина: {}\nДлина: {}\nКол-во: {}\nЦвет: {}\nRoll Number: {}\n\nВведите промежуточный результат:".format(
                product.id,
                product.profile,
                product.width,
                product.thickness,
                product.length,
                product.quantity,
                product.color,
                product.roll_number,
            )
        ),
        reply_markup=kbc.results_keyboard(),
    )


@router.callback_query(F.data == "10_products", MainStates.enter_result)
async def handle_10_products(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (order_id := storage_data.get("order_id")) is None:
        return
    if (bundle_id := storage_data.get("bundle_id")) is None:
        return

    plan = Plan.get_plan()
    order = plan.get_order(order_id)
    bundle = order.get_bundle(bundle_id)

    # TODO: тут что-то происходит...

    await callback.answer(loc.get_text("Добавлено 10 изделий / метров"))


@router.callback_query(F.data == "input_count", MainStates.enter_result)
async def handle_input_count_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.input_count)
    await callback.message.answer(
        loc.get_text("Введите кол-во изготовленных изделий:")
    )


@router.message(F.text, MainStates.input_count)
async def handle_count_input(message: Message, state: FSMContext) -> None:
    kbc = KeyboardCollection()
    if helpers.is_int(message.text) or helpers.is_float(message.text):
        # TODO: тут что-то происходит...
        await message.answer(
            loc.get_text(f"Вы ввели {message.text}"),
            reply_markup=kbc.return_keyboard(),
        )
    else:
        await message.answer(loc.get_text(f"Нужно ввести число"))


@router.callback_query(F.data == "finish_bundle", MainStates.enter_result)
async def handle_finish_bundle_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    # TODO: тут что-то происходит...
    await handle_chosen_order(callback, state)


@router.callback_query(
    F.data == "finish_shift",
    StateFilter(
        MainStates.choose_order,
        MainStates.choose_bundle,
        MainStates.choose_product,
        MainStates.enter_result,
    ),
)
async def handle_finish_shift(
    callback: CallbackQuery, state: FSMContext
) -> None:
    # TODO: тут что-то происходит...
    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.input_count)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(
            "За эту смену:\n- Вы произвели ... тонн изделий;\n- Вы заработали ... рублей;\n- Линия простаивала ... минут."
        ),
    )
    await handle_chosen_line(callback, state)


@router.callback_query(
    F.data == "idle",
    StateFilter(
        MainStates.choose_order,
        MainStates.choose_bundle,
        MainStates.choose_product,
        MainStates.enter_result,
    ),
)
async def handle_idle_btn(callback: CallbackQuery, state: FSMContext) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.idle)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text("Выберите тип простоя:"), reply_markup=kbc.idle_keyboard()
    )


@router.callback_query(
    F.data.in_({IdleType.SCHEDULED, IdleType.UNSCHEDULED}), MainStates.idle
)
async def handle_idle_type(callback: CallbackQuery, state: FSMContext) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(MainStates.idle_option)

    kbc = KeyboardCollection()
    if callback.data == IdleType.SCHEDULED:
        keyboard = kbc.scheduled_idle_keyboard()
    elif callback.data == IdleType.UNSCHEDULED:
        keyboard = kbc.unscheduled_idle_keyboard()
    else:
        return

    await callback.message.answer(
        loc.get_text("Выберите вариант:"), reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("idle"), MainStates.idle_option)
async def handle_idle_type(callback: CallbackQuery, state: FSMContext) -> None:
    await helpers.try_delete_message(callback.message)
    data = callback.data.split(":")
    idle_type = data[1]
    idle_option = data[2]

    # TODO: тут что-то происходит...

    await callback.message.answer(loc.get_text("Линия простаивает"))
    await handle_chosen_line(callback, state)


@router.callback_query(
    F.data == "return",
    StateFilter(
        MainStates.input_count, MainStates.idle, MainStates.idle_option
    ),
)
async def handle_return(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    match current_state:
        case MainStates.input_count:
            await handle_chosen_product(callback, state)
        case MainStates.idle:
            await choose_line(callback.message, state)
        case MainStates.idle_option:
            await handle_idle_btn(callback, state)
