from functools import partial

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram_widgets.types import AdditionalButtonsType, ButtonType

from app import callbacks
from app.enums import IdleReason, IdleType
from app.models import Bundle, Operator, Order, Product, ProductionLine
from loaders import loc


class KeyboardCollection:
    def __init__(self, lang: str = "ru") -> None:
        self._language = lang

    def _inline(self, text_key: str, callback_data: str) -> InlineKeyboardButton:
        button_text = loc.get_text(text_key, self._language)
        return InlineKeyboardButton(text=button_text, callback_data=callback_data)

    def inline_return_button(self) -> InlineKeyboardButton:
        return self._inline(text_key="button/RETURN", callback_data="return")

    def return_button_row(self) -> AdditionalButtonsType:
        return [[self.inline_return_button()]]

    def return_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self.inline_return_button())
        builder.adjust(1)
        return builder.as_markup()

    def continue_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self._inline(text_key="button/CONTINUE", callback_data="return"))
        builder.adjust(1)
        return builder.as_markup()

    def yes_no_keyboard(self, return_button: bool = False) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            self._inline(text_key="button/YES", callback_data="yes"),
            self._inline(text_key="button/NO", callback_data="no"),
        )
        if return_button:
            builder.add(self.inline_return_button())
        builder.adjust(2, 1)
        return builder.as_markup()

    def contact_keyboard(self) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(
                text=loc.get_text("button/SEND_CONTACT", self._language),
                request_contact=True,
            )
        )
        return builder.as_markup(resize_keyboard=True)

    def terms_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            self._inline(text_key="button/AGREE", callback_data="terms_agree"),
            self._inline(text_key="button/DISAGREE", callback_data="terms_disagree"),
        )
        builder.adjust(2)
        return builder.as_markup()

    def language_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🇷🇺Русский", callback_data="language ru")
        builder.button(text="🇺🇸English", callback_data="language en")
        builder.adjust(2)
        return builder.as_markup()

    def choose_line_keyboard(self, lines: list[ProductionLine]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for line in lines:
            if line.id is not None:
                builder.button(text=line.name, callback_data=callbacks.Line(id=line.id))
        builder.adjust(1)
        return builder.as_markup()

    def operator_buttons(self, operators: list[Operator]) -> list[ButtonType]:
        return [InlineKeyboardButton(
            text=operator.name, callback_data=callbacks.Operator(id=operator.id).pack(),
        ) for operator in operators if operator.id is not None]

    def choose_action_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            self._inline(text_key="button/START_SHIFT", callback_data="start_shift"),
            self.inline_return_button(),
        )
        builder.adjust(1)
        return builder.as_markup()

    def choose_order_keyboard(self, orders: list[Order]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for order in orders:
            if order.id is not None:
                builder.button(text=order.name, callback_data=callbacks.Order(id=order.id))
        builder.add(
            self._inline(text_key="button/FINISH_SHIFT", callback_data="finish_shift"),
            self._inline(text_key="button/IDLE", callback_data="idle"),
        )
        builder.adjust(1)
        return builder.as_markup()

    def choose_bundle_keyboard(self, bundles: list[Bundle]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for bundle in bundles:
            if bundle.id is not None:
                builder.button(text=bundle.native_id, callback_data=callbacks.Bundle(id=bundle.id))
        builder.add(
            self._inline(text_key="button/FINISH_SHIFT", callback_data="finish_shift"),
            self._inline(text_key="button/IDLE", callback_data="idle"),
            self.inline_return_button(),
        )
        builder.adjust(1)
        return builder.as_markup()

    def choose_product_keyboard(self, products: list[Product]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for product in products:
            if product.id is not None:
                callback_data = callbacks.Product(id=product.id)
                builder.button(text=product.native_id, callback_data=callback_data)
        builder.add(
            self._inline(text_key="button/FINISH_BUNDLE", callback_data="finish_bundle"),
            self._inline(text_key="button/FINISH_SHIFT", callback_data="finish_shift"),
            self._inline(text_key="button/IDLE", callback_data="idle"),
            self.inline_return_button(),
        )
        builder.adjust(1)
        return builder.as_markup()

    def results_keyboard(self, products_left: int = 10) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        quantity = 10 if products_left > 10 else products_left
        if quantity > 1:
            builder.button(
                text=loc.get_text("button/FINISH_PRODUCTS", quantity),
                callback_data=callbacks.FinishProducts(quantity=quantity),
            )
        builder.add(
            self._inline(text_key="button/OTHER_COUNT", callback_data="input_count"),
            self._inline(text_key="button/FINISH_PRODUCT", callback_data="finish_product"),
            self._inline(text_key="button/FINISH_SHIFT", callback_data="finish_shift"),
            self._inline(text_key="button/IDLE", callback_data="idle"),
            self.inline_return_button(),
        )
        builder.adjust(1)
        return builder.as_markup()

    def idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/SCHEDULED_IDLE"),
            callback_data=callbacks.Idle(type=IdleType.SCHEDULED),
        )
        builder.button(
            text=loc.get_text("button/UNSCHEDULED_IDLE"),
            callback_data=callbacks.Idle(type=IdleType.UNSCHEDULED),
        )
        builder.add(self.inline_return_button())
        builder.adjust(1)
        return builder.as_markup()

    def scheduled_idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        sheduled = partial(callbacks.IdleOption, type=IdleType.SCHEDULED)
        builder.button(
            text=loc.get_text("button/REPAIR"),
            callback_data=sheduled(reason=IdleReason.REPAIR),
        )
        builder.button(
            text=loc.get_text("button/NO_ORDERS"),
            callback_data=sheduled(reason=IdleReason.NO_ORDERS),
        )
        builder.button(
            text=loc.get_text("button/COIL_REPLACE"),
            callback_data=sheduled(reason=IdleReason.COIL_REPLACE),
        )
        builder.add(self.inline_return_button())
        builder.adjust(1)
        return builder.as_markup()

    def unscheduled_idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        unsheduled = partial(callbacks.IdleOption, type=IdleType.UNSCHEDULED)
        builder.button(
            text=loc.get_text("button/BREAKDOWN"),
            callback_data=unsheduled(reason=IdleReason.BREAKDOWN),
        )
        builder.button(
            text=loc.get_text("button/OTHER_REASON"),
            callback_data=unsheduled(reason=IdleReason.OTHER),
        )
        builder.add(self.inline_return_button())
        builder.adjust(1)
        return builder.as_markup()

    def finish_idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self._inline(text_key="button/FINISH_IDLE", callback_data="finish_idle"))
        builder.adjust(1)
        return builder.as_markup()

    def admin_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self._inline(text_key="button/ADD_OPERATOR", callback_data="add_operator"))
        builder.add(self._inline(text_key="button/ADD_ACCOUNT", callback_data="add_account"))
        builder.adjust(1)
        return builder.as_markup()
