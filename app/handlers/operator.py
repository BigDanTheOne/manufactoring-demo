import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_widgets.pagination import KeyboardPaginator

from app import callbacks
from app.enums import IdleType, UserRole
from app.extras import helpers
from app.filters import UserRoleFilter
from app.keyboards import KeyboardCollection
from app.models import (
    Bundle,
    Operator,
    Order,
    Plan,
    Product,
    ProductionLine,
)
from app.states import AccountStates
from loaders import bot, loc

logger = logging.getLogger()

router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(UserRoleFilter(UserRole.OPERATOR))
router.callback_query.filter(UserRoleFilter(UserRole.OPERATOR))


async def choose_line(obj: Message | CallbackQuery, state: FSMContext) -> None:
    logger.debug("choose_line")
    if isinstance(obj, CallbackQuery):
        await helpers.hide_markup_or_delete(obj)
    if (message := helpers.resolve_message(obj)) is None:
        return

    await state.set_state(AccountStates.choose_line)
    lines = await ProductionLine.all().to_list()
    await message.answer(
        loc.get_text("operator/choose_line"),
        reply_markup=KeyboardCollection().choose_line_keyboard(lines),
    )


@router.callback_query(callbacks.Line.filter(), AccountStates.choose_line)
async def handle_chosen_line(
    callback: CallbackQuery, state: FSMContext, callback_data: callbacks.Line | None = None
) -> None:
    logger.debug("handle_chosen_line")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return
    if callback_data is not None:
        line_id = callback_data.id
        await state.update_data(line_id=str(line_id))
    else:
        storage_data = await state.get_data()
        line_id = storage_data.get("line_id")

    if (line := await ProductionLine.get(line_id)) is None:
        return

    await state.set_state(AccountStates.choose_operator)
    operators = await Operator.find(Operator.line_id == line.id).to_list()

    kbc = KeyboardCollection()
    operator_buttons = kbc.operator_buttons(operators)
    paginator = KeyboardPaginator(
        data=operator_buttons,
        router=router,
        per_page=10,
        per_row=2,
        additional_buttons=kbc.return_button_row(),
    )

    await message.answer(
        loc.get_text("operator/choose_operator"), reply_markup=paginator.as_markup()
    )


@router.callback_query(callbacks.Operator.filter(), AccountStates.choose_operator)
async def handle_chosen_operator(
    callback: CallbackQuery, state: FSMContext, callback_data: callbacks.Operator
) -> None:
    logger.debug("handle_chosen_operator")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    operator_id = callback_data.id
    await state.update_data(operator_id=str(operator_id))
    if (operator := await Operator.get(operator_id)) is None:
        return

    await state.set_state(AccountStates.choose_action)
    await message.answer(
        loc.get_text("operator/operator_profile", operator.name),
        reply_markup=KeyboardCollection().choose_action_keyboard(),
    )


@router.callback_query(F.data == "start_shift", AccountStates.choose_action)
async def handle_start_shift_btn(callback: CallbackQuery, state: FSMContext) -> None:
    logger.debug("handle_start_shift_btn")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    await state.update_data(order_id=None, bundle_id=None)

    storage_data = await state.get_data()
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return
    if (plan := await Plan.get_current()) is None:
        await callback.answer(loc.get_text("operator/no_plan"))
        return

    await state.set_state(AccountStates.choose_order)
    orders = await plan.get_active_orders()
    text = loc.get_text("operator/choose_order")
    if not orders:
        text = loc.get_text("operator/no_orders")
    await operator.start_shift()
    if len(orders) == 1:
        await state.update_data(order_id=str(orders[0].id))
        await handle_chosen_order(
            callback, state, prefix_text=loc.get_text("operator/chosen_order")
        )
        return

    kbc = KeyboardCollection()
    await message.answer(text, reply_markup=kbc.choose_order_keyboard(orders=orders))


@router.callback_query(callbacks.Order.filter(), AccountStates.choose_order)
async def handle_chosen_order(
    callback: CallbackQuery,
    state: FSMContext,
    callback_data: callbacks.Order | None = None,
    prefix_text: str = "",
) -> None:
    logger.debug("handle_chosen_order")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    if callback_data is not None:
        order_id = callback_data.id
        await state.update_data(order_id=str(order_id), bundle_id=None)
    else:
        storage_data = await state.get_data()
        order_id = storage_data.get("order_id")
        await state.update_data(bundle_id=None)

    if (order := await Order.get(order_id)) is None:
        await callback.answer(loc.get_text("operator/order_not_found"))
        return

    order_info = prefix_text + loc.get_text(
        "operator/order_info",
        order.name,
        order.production_line_id,
        order.total_mass,
        order.total_length,
        order.execution_time,
    )
    bundles = await order.get_active_bundles()
    if not bundles:
        order.finished = True
        await order.save()
        await message.answer(loc.get_text("operator/order_done", order.name))
        await handle_start_shift_btn(callback, state)
        return
    await state.set_state(AccountStates.choose_bundle)
    if len(bundles) == 1:
        await state.update_data(bundle_id=str(bundles[0].id))
        await handle_chosen_bundle(
            callback, state, prefix_text=order_info + loc.get_text("operator/chosen_bundle")
        )
        return

    await message.answer(
        order_info + loc.get_text("operator/choose_bundle"),
        reply_markup=KeyboardCollection().choose_bundle_keyboard(bundles),
    )


@router.callback_query(callbacks.Bundle.filter(), AccountStates.choose_bundle)
async def handle_chosen_bundle(
    callback: CallbackQuery,
    state: FSMContext,
    callback_data: callbacks.Bundle | None = None,
    prefix_text: str = "",
) -> None:
    logger.debug("handle_chosen_bundle")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    if callback_data is not None:
        bundle_id = callback_data.id
        await state.update_data(bundle_id=str(bundle_id), product_id=None)
    else:
        storage_data = await state.get_data()
        bundle_id = storage_data.get("bundle_id")
        await state.update_data(product_id=None)

    if (bundle := await Bundle.get(bundle_id)) is None:
        await callback.answer(loc.get_text("operator/bundle_not_found"))
        return

    bundle_info = prefix_text + loc.get_text(
        "operator/bundle_info",
        bundle.native_id,
        bundle.total_mass,
        bundle.total_length,
        bundle.execution_time,
    )
    products = await bundle.get_active_products()
    if not products:
        bundle.finished = True
        await bundle.save()
        await message.answer(loc.get_text("operator/bundle_done", bundle.native_id))
        await handle_chosen_order(callback, state)
        return
    await state.set_state(AccountStates.choose_product)
    if len(products) == 1:
        await state.update_data(product_id=str(products[0].id))
        await handle_chosen_product(
            callback, state, prefix_text=bundle_info + loc.get_text("operator/chosen_product")
        )
        return

    await message.answer(
        bundle_info + loc.get_text("operator/choose_product"),
        reply_markup=KeyboardCollection().choose_product_keyboard(products),
    )


@router.callback_query(callbacks.Product.filter(), AccountStates.choose_product)
async def handle_chosen_product(
    callback: CallbackQuery,
    state: FSMContext,
    callback_data: callbacks.Product | None = None,
    prefix_text: str = "",
) -> None:
    logger.debug("handle_chosen_product")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    if callback_data is not None:
        product_id = callback_data.id
        await state.update_data(product_id=str(product_id))
    else:
        storage_data = await state.get_data()
        product_id = storage_data.get("product_id")

    if (product := await Product.get(product_id)) is None:
        await callback.answer(loc.get_text("operator/product_not_found"))
        return

    product_info = prefix_text + loc.get_text(
        "operator/product_info",
        product.native_id,
        product.profile,
        product.width,
        product.thickness,
        product.length,
        product.quantity,
        product.color,
        product.roll_number,
    )

    if product.quantity == 0:
        await message.answer(loc.get_text("operator/product_done", product.native_id))
        await handle_chosen_bundle(callback, state)
        return

    await state.set_state(AccountStates.enter_result)
    product_msg = await message.answer(
        product_info + loc.get_text("operator/enter_result"),
        reply_markup=KeyboardCollection().results_keyboard(products_left=product.quantity),
    )
    await state.update_data(product_message_id=product_msg.message_id)


@router.callback_query(callbacks.FinishProducts.filter(), AccountStates.enter_result)
async def handle_finish_products(
    callback: CallbackQuery, state: FSMContext, callback_data: callbacks.FinishProducts
) -> None:
    logger.debug("handle_finish_products")
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        return
    if (product := await Product.get(product_id)) is None:
        await callback.answer(loc.get_text("operator/product_not_found"))
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return
    if (product_message_id := storage_data.get("product_message_id")) is None:
        return
    if (message := helpers.resolve_message(callback)) is None:
        return

    quantity = callback_data.quantity
    if product.quantity < quantity:
        await callback.answer(
            loc.get_text("operator/wrong_product_count", product.quantity), show_alert=True
        )
        return

    await state.set_state(AccountStates.enter_result)
    product.quantity -= quantity
    await product.save()

    await operator.log_progress(product, count=quantity)

    if product.quantity == 0:
        await message.answer(loc.get_text("operator/product_done", product.native_id))
        await handle_chosen_bundle(callback, state)
        return

    product_info = loc.get_text(
        "operator/product_info",
        product.native_id,
        product.profile,
        product.width,
        product.thickness,
        product.length,
        product.quantity,
        product.color,
        product.roll_number,
    )

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=product_message_id,
        text=product_info + loc.get_text("operator/enter_result"),
        reply_markup=KeyboardCollection().results_keyboard(products_left=product.quantity),
    )
    await callback.answer(loc.get_text("operator/results/product_added", quantity))


@router.callback_query(F.data == "input_count", AccountStates.enter_result)
async def handle_input_count_btn(callback: CallbackQuery, state: FSMContext) -> None:
    logger.debug("handle_input_count_btn")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return
    await state.set_state(AccountStates.input_count)
    await message.answer(loc.get_text("operator/results/enter_count"))


@router.message(F.text, AccountStates.input_count)
async def handle_count_input(message: Message, state: FSMContext) -> None:
    logger.debug("handle_count_input")
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return

    kbc = KeyboardCollection()
    if (product := await Product.get(product_id)) is None:
        await message.answer(
            loc.get_text("operator/product_not_found"), reply_markup=kbc.return_keyboard(),
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

    await operator.log_progress(product, count)

    await message.answer(
        loc.get_text("operator/product_added", message.text),
        reply_markup=kbc.continue_keyboard(),
    )


@router.callback_query(F.data == "finish_product", AccountStates.enter_result)
async def handle_finish_product_btn(callback: CallbackQuery, state: FSMContext) -> None:
    logger.debug("handle_finish_product_btn")
    if (message := helpers.resolve_message(callback)) is None:
        return
    storage_data = await state.get_data()
    if (product_id := storage_data.get("product_id")) is None:
        return
    if (product := await Product.get(product_id)) is None:
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    product.quantity = 0
    await product.save()

    await operator.log_progress(product, product.quantity)

    await message.answer(loc.get_text("operator/product_done", product.native_id))
    await handle_chosen_bundle(callback, state)


@router.callback_query(F.data == "finish_bundle", AccountStates.choose_product)
async def handle_finish_bundle_btn(callback: CallbackQuery, state: FSMContext) -> None:
    logger.debug("handle_finish_bundle_btn")
    if (message := helpers.resolve_message(callback)) is None:
        return
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
        await operator.log_progress(product, product.quantity)
        product.quantity = 0
        await product.save()

    bundle.finished = True
    await bundle.save()

    await message.answer(loc.get_text("operator/bundle_done", bundle.native_id))
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
async def handle_finish_shift(callback: CallbackQuery, state: FSMContext) -> None:
    logger.debug("handle_finish_shift")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    storage_data = await state.get_data()
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return
    if (line_id := storage_data.get("line_id")) is None:
        return
    if (line := await ProductionLine.get(line_id)) is None:
        return
    if (plan := await Plan.get_current()) is None:
        return

    await state.set_state(AccountStates.input_count)
    await operator.finish_shift()

    plan_ton = plan.total_mass / 1_000_000
    produced_ton = operator.shift_mass_produced / 1_000_000
    income = produced_ton / plan_ton * operator.rate

    produced_rounded = round(produced_ton, 4)
    income_rounded = round(income, 2)

    line_idle_duration = round(line.get_idle_duration_today() / 60, 1)

    await message.answer(
        loc.get_text("operator/finish_shift", produced_rounded, income_rounded, line_idle_duration)
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
    logger.debug("handle_idle_btn")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    current_state = await state.get_state()
    await state.update_data(state_before_idle=current_state)

    await state.set_state(AccountStates.idle)
    await message.answer(
        loc.get_text("operator/choose_idle_type"),
        reply_markup=KeyboardCollection().idle_keyboard(),
    )


# @router.callback_query(F.data.in_({IdleType.SCHEDULED, IdleType.UNSCHEDULED}), AccountStates.idle)
@router.callback_query(callbacks.Idle.filter(), AccountStates.idle)
async def handle_idle_type(
    callback: CallbackQuery, state: FSMContext, callback_data: callbacks.Idle
) -> None:
    logger.debug("handle_idle_type")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    await state.set_state(AccountStates.idle_option)
    if callback_data.type == IdleType.SCHEDULED:
        keyboard = KeyboardCollection().scheduled_idle_keyboard()
    elif callback_data.type == IdleType.UNSCHEDULED:
        keyboard = KeyboardCollection().unscheduled_idle_keyboard()
    else:
        return
    await message.answer(loc.get_text("operator/choose_idle_option"), reply_markup=keyboard)


# @router.callback_query(F.data.startswith("idle"), AccountStates.idle_option)
@router.callback_query(callbacks.IdleOption.filter(), AccountStates.idle_option)
async def handle_idle_reason(
    callback: CallbackQuery, state: FSMContext, callback_data: callbacks.IdleOption
) -> None:
    logger.debug("handle_idle_reason")
    if (message := await helpers.hide_markup_or_delete(callback)) is None:
        return

    storage_data = await state.get_data()
    if (line_id := storage_data.get("line_id")) is None:
        return
    if (line := await ProductionLine.get(line_id)) is None:
        return
    if (operator_id := storage_data.get("operator_id")) is None:
        return
    if (operator := await Operator.get(operator_id)) is None:
        return

    await state.set_state(AccountStates.idle_now)
    idle_type = callback_data.type
    idle_reason = callback_data.reason
    await line.start_idle(operator_id=operator.id, type=idle_type, reason=idle_reason)
    await message.answer(
        loc.get_text("operator/idle_line"),
        reply_markup=KeyboardCollection().finish_idle_keyboard(),
    )


@router.callback_query(F.data == "finish_idle", AccountStates.idle_now)
async def handle_finish_idle(callback: CallbackQuery, state: FSMContext) -> None:
    logger.debug("handle_finish_idle")
    if (message := helpers.resolve_message(callback)) is None:
        return
    storage_data = await state.get_data()
    if (line_id := storage_data.get("line_id")) is None:
        return
    if (line := await ProductionLine.get(line_id)) is None:
        return

    await line.finish_idle()
    await message.answer(loc.get_text("operator/line_restored"))

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
    logger.debug("handle_return")
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
        case AccountStates.idle | AccountStates.choose_operator | AccountStates.choose_action:
            await choose_line(callback, state)
        case AccountStates.idle_option:
            await handle_idle_btn(callback, state)
