from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram_widgets.pagination import KeyboardPaginator

from app.extras import helpers
from app.enums import IdleType, UserRole
from app.filters import UserRoleFilter
from app.models import (
    ProdutionLine,
    Operator,
    ProgressLog,
    Plan,
    Order,
    Bundle,
    Product,
)
from app.keyboards import KeyboardCollection
from app.states import AccountStates
from loaders import loc, bot


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(UserRoleFilter(UserRole.OPERATOR))
router.callback_query.filter(UserRoleFilter(UserRole.OPERATOR))


async def choose_line(message: Message, state: FSMContext) -> None:
    await helpers.try_delete_message(message)
    await state.set_state(AccountStates.choose_line)

    lines = await ProdutionLine.all().to_list()
    kbc = KeyboardCollection()

    await message.answer(
        loc.get_text("operator/choose_line"),
        reply_markup=kbc.choose_line_keyboard(lines),
    )


@router.callback_query(F.data.startswith("line"), AccountStates.choose_line)
async def handle_chosen_line(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (line_id := storage_data.get("line_id")) is None:
        line_id = callback.data.split(":")[1]
    await state.update_data(line_id=line_id)
    if (line := await ProdutionLine.get(line_id)) is None:
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.choose_operator)

    kbc = KeyboardCollection()
    operator_buttons = await kbc.operator_buttons(line)
    paginator = KeyboardPaginator(
        data=operator_buttons,
        router=router,
        per_page=10,
        per_row=2,
        additional_buttons=kbc.return_button_row(),
    )

    await callback.message.answer(
        loc.get_text("operator/choose_operator"),
        reply_markup=paginator.as_markup(),
    )


@router.callback_query(
    F.data.startswith("operator"), AccountStates.choose_operator
)
async def handle_chosen_operator(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (operator_id := storage_data.get("operator_id")) is None:
        operator_id = callback.data.split(":")[1]
        await state.update_data(operator_id=operator_id)

    if (operator := await Operator.get(operator_id)) is None:
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.choose_action)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text("operator/operator_profile", operator.name),
        reply_markup=kbc.choose_action_keyboard(),
    )


@router.callback_query(F.data == "start_shift", AccountStates.choose_action)
async def handle_start_shift_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await state.update_data(order_id=None)
    await state.update_data(bundle_id=None)

    storage_data = await state.get_data()
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return
    if (plan := await Plan.get_current()) is None:
        await callback.answer(
            loc.get_text("operator/no_plan"),
        )
        return

    orders = await plan.get_active_orders()
    if not orders:
        await callback.message.answer(loc.get_text("operator/no_orders"))
        await choose_line(callback.message, state)
        return

    await operator.start_shift()

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.choose_order)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text("operator/choose_order"),
        reply_markup=kbc.choose_order_keyboard(orders=orders),
    )


@router.callback_query(F.data.startswith("order"), AccountStates.choose_order)
async def handle_chosen_order(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (order_id := storage_data.get("order_id")) is None:
        order_id = callback.data.split(":")[1]
    await state.update_data(order_id=order_id)
    await state.update_data(bundle_id=None)

    if (order := await Order.get(order_id)) is None:
        await callback.answer(
            loc.get_text("operator/order_not_found"),
        )
        return
    bundles = await order.get_active_bundles()

    if not bundles:
        order.finished = True
        await order.save()
        await callback.message.answer(
            loc.get_text("operator/order_done", order.name)
        )
        await handle_start_shift_btn(callback, state)
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.choose_bundle)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(
            "operator/choose_bundle",
            order.name,
            order.production_line_id,
            order.total_mass,
            order.total_length,
            order.execution_time,
        ),
        reply_markup=kbc.choose_bundle_keyboard(bundles),
    )


@router.callback_query(
    F.data.startswith("bundle"), AccountStates.choose_bundle
)
async def handle_chosen_bundle(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (bundle_id := storage_data.get("bundle_id")) is None:
        bundle_id = callback.data.split(":")[1]
    await state.update_data(bundle_id=bundle_id)
    await state.update_data(product_id=None)

    if (bundle := await Bundle.get(bundle_id)) is None:
        await callback.answer(
            loc.get_text("operator/bundle_not_found"),
        )
        return
    products = await bundle.get_active_products()

    if not products:
        bundle.finished = True
        await bundle.save()
        await callback.message.answer(
            loc.get_text("operator/bundle_done", bundle.native_id)
        )
        await handle_chosen_order(callback, state)
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.choose_product)

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text(
            "operator/choose_product",
            bundle.native_id,
            bundle.total_mass,
            bundle.total_length,
            bundle.execution_time,
        ),
        reply_markup=kbc.choose_product_keyboard(products),
    )


@router.callback_query(
    F.data.startswith("product"), AccountStates.choose_product
)
async def handle_chosen_product(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        product_id = callback.data.split(":")[1]
    await state.update_data(product_id=product_id)

    if (product := await Product.get(product_id)) is None:
        await callback.answer(
            loc.get_text("operator/product_not_found"),
        )
        return

    if product.quantity == 0:
        await callback.message.answer(
            loc.get_text("operator/product_done", product.native_id)
        )
        await handle_chosen_bundle(callback, state)
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.enter_result)

    kbc = KeyboardCollection()
    product_msg = await callback.message.answer(
        loc.get_text(
            "operator/enter_result",
            product.native_id,
            product.profile,
            product.width,
            product.thickness,
            product.length,
            product.quantity,
            product.color,
            product.roll_number,
        ),
        reply_markup=kbc.results_keyboard(),
    )
    await state.update_data(product_message_id=product_msg.message_id)


@router.callback_query(F.data == "10_products", AccountStates.enter_result)
async def handle_10_products(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        return
    await state.update_data(product_id=product_id)
    if (product := await Product.get(product_id)) is None:
        await callback.answer(
            loc.get_text("operator/product_not_found"),
        )
        return

    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    if (product_message_id := storage_data.get("product_message_id")) is None:
        return

    await state.set_state(AccountStates.enter_result)

    if product.quantity < 10:
        await callback.answer(
            loc.get_text("operator/wrong_product_count", product.quantity),
            show_alert=True,
        )
        return

    product.quantity -= 10
    await product.save()

    operator.progress_log.append(
        ProgressLog(product_id=product.id, count=10, date=datetime.now())
    )
    await operator.save()

    if product.quantity == 0:
        await callback.message.answer(
            loc.get_text("operator/product_done", product.native_id)
        )
        await handle_chosen_bundle(callback, state)
        return

    kbc = KeyboardCollection()
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=product_message_id,
        text=loc.get_text(
            "operator/enter_result",
            product.native_id,
            product.profile,
            product.width,
            product.thickness,
            product.length,
            product.quantity,
            product.color,
            product.roll_number,
        ),
        reply_markup=kbc.results_keyboard(),
    )

    await callback.answer(loc.get_text("operator/results/10_products_added"))


@router.callback_query(F.data == "input_count", AccountStates.enter_result)
async def handle_input_count_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.input_count)
    await callback.message.answer(loc.get_text("operator/results/enter_count"))


@router.message(F.text, AccountStates.input_count)
async def handle_count_input(message: Message, state: FSMContext) -> None:
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    await state.update_data(product_id=product_id)

    kbc = KeyboardCollection()
    if (product := await Product.get(product_id)) is None:
        await message.answer(
            loc.get_text("operator/product_not_found"),
            reply_markup=kbc.return_keyboard(),
        )
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    if helpers.is_int(message.text):
        count = int(message.text)
    elif helpers.is_float(message.text):
        count = float(message.text)
    else:
        await message.answer(loc.get_text("operator/results/number_required"))
        return

    if product.quantity < count:
        await message.answer(
            loc.get_text("operator/wrong_product_count", product.quantity),
            reply_markup=kbc.return_keyboard(),
        )
        return

    product.quantity -= count
    await product.save()

    operator.progress_log.append(
        ProgressLog(product_id=product.id, count=count, date=datetime.now())
    )
    await operator.save()

    await message.answer(
        loc.get_text("operator/product_added", message.text),
        reply_markup=kbc.continue_keyboard(),
    )


@router.callback_query(F.data == "finish_product", AccountStates.enter_result)
async def handle_finish_bundle_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        return
    if (product := await Product.get(product_id)) is None:
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    operator.progress_log.append(
        ProgressLog(
            product_id=product.id, count=product.quantity, date=datetime.now()
        )
    )
    product.quantity = 0
    await product.save()
    await operator.save()
    await callback.message.answer(
        loc.get_text("operator/product_done", product.native_id)
    )
    await handle_chosen_bundle(callback, state)


@router.callback_query(F.data == "finish_bundle", AccountStates.choose_product)
async def handle_finish_bundle_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (bundle_id := storage_data.get("bundle_id")) is None:
        return
    if (bundle := await Bundle.get(bundle_id)) is None:
        return

    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    for product_id in bundle.products:
        if (product := await Product.get(product_id)) is None:
            continue
        operator.progress_log.append(
            ProgressLog(
                product_id=product.id,
                count=product.quantity,
                date=datetime.now(),
            )
        )
        product.quantity = 0
        await product.save()
        await operator.save()
    bundle.finished = True
    await bundle.save()
    await callback.message.answer(
        loc.get_text("operator/bundle_done", bundle.native_id)
    )
    await handle_chosen_order(callback, state)


@router.callback_query(
    F.data == "finish_shift",
    StateFilter(
        AccountStates.choose_order,
        AccountStates.choose_bundle,
        AccountStates.choose_product,
        AccountStates.enter_result,
    ),
)
async def handle_finish_shift(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    await operator.finish_shift()

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.input_count)

    await callback.message.answer(
        loc.get_text("operator/finish_shift", 0, 0, 0),
    )
    await handle_chosen_line(callback, state)


@router.callback_query(
    F.data == "idle",
    StateFilter(
        AccountStates.choose_order,
        AccountStates.choose_bundle,
        AccountStates.choose_product,
        AccountStates.enter_result,
    ),
)
async def handle_idle_btn(callback: CallbackQuery, state: FSMContext) -> None:
    await helpers.try_delete_message(callback.message)
    current_state = await state.get_state()
    await state.update_data(state_before_idle=current_state)

    await state.set_state(AccountStates.idle)
    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text("operator/choose_idle_type"),
        reply_markup=kbc.idle_keyboard(),
    )


@router.callback_query(
    F.data.in_({IdleType.SCHEDULED, IdleType.UNSCHEDULED}), AccountStates.idle
)
async def handle_idle_type(callback: CallbackQuery, state: FSMContext) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.idle_option)

    kbc = KeyboardCollection()
    if callback.data == IdleType.SCHEDULED:
        keyboard = kbc.scheduled_idle_keyboard()
    elif callback.data == IdleType.UNSCHEDULED:
        keyboard = kbc.unscheduled_idle_keyboard()
    else:
        return

    await callback.message.answer(
        loc.get_text("operator/choose_idle_option"), reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("idle"), AccountStates.idle_option)
async def handle_idle_type(callback: CallbackQuery, state: FSMContext) -> None:
    data = callback.data.split(":")
    idle_type = data[1]
    idle_reason = data[2]

    storage_data = await state.get_data()
    if (line_id := storage_data.get("line_id")) is None:
        return
    if (line := await ProdutionLine.get(line_id)) is None:
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    await helpers.try_delete_message(callback.message)
    await state.set_state(AccountStates.idle_now)

    await line.start_idle(
        operator_id=operator.id, type=idle_type, reason=idle_reason
    )

    kbc = KeyboardCollection()
    await callback.message.answer(
        loc.get_text("operator/idle_line"),
        reply_markup=kbc.finish_idle_keyboard(),
    )


@router.callback_query(F.data == "finish_idle", AccountStates.idle_now)
async def handle_finish_idle(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (line_id := storage_data.get("line_id")) is None:
        return
    if (line := await ProdutionLine.get(line_id)) is None:
        return

    await line.finish_idle()

    await callback.message.answer(loc.get_text("operator/line_restored"))

    last_state = storage_data.get("state_before_idle")
    match last_state:
        case AccountStates.enter_result.state:
            await handle_chosen_product(callback, state)
        case AccountStates.choose_product.state:
            await handle_chosen_bundle(callback, state)
        case AccountStates.choose_bundle.state:
            await handle_chosen_order(callback, state)
        case AccountStates.choose_order.state:
            await handle_start_shift_btn(callback, state)
        case _:
            await handle_chosen_line(callback, state)


@router.callback_query(
    F.data == "return",
    StateFilter(
        AccountStates.choose_action,
        AccountStates.enter_result,
        AccountStates.choose_product,
        AccountStates.choose_bundle,
        AccountStates.choose_operator,
        AccountStates.input_count,
        AccountStates.idle,
        AccountStates.idle_option,
    ),
)
async def handle_return(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    match current_state:
        case AccountStates.enter_result:
            await handle_chosen_bundle(callback, state)
        case AccountStates.choose_product:
            await handle_chosen_order(callback, state)
        case AccountStates.choose_bundle:
            await handle_start_shift_btn(callback, state)
        case AccountStates.input_count:
            await handle_chosen_product(callback, state)
        case (
            AccountStates.idle
            | AccountStates.choose_operator
            | AccountStates.choose_action
        ):
            await choose_line(callback.message, state)
        case AccountStates.idle_option:
            await handle_idle_btn(callback, state)
