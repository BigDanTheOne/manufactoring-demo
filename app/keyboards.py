from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from beanie import PydanticObjectId

from app.enums import (
    IdleType,
    ProductionLine,
    ScheduledIdleReason,
    UnscheduledIdleReason,
)
from app.models import Bundle, Operator, Order, Product, ProdutionLine
from loaders import loc


class LineCallback(CallbackData, prefix="line"):
    id: PydanticObjectId


class KeyboardCollection:
    def __init__(self, lang: str = "ru") -> None:
        self._language = lang

    def _inline_button(self, text_key: str, callback_data: str) -> InlineKeyboardButton:
        button_text = loc.get_text(text_key, self._language)
        return InlineKeyboardButton(text=button_text, callback_data=callback_data)

    def return_button(self) -> InlineKeyboardButton:
        return self._inline_button(text_key="button/RETURN", callback_data="return")

    def return_button_row(self) -> list[list[InlineKeyboardButton]]:
        return [[self.return_button()]]

    def return_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def continue_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self._inline_button(text_key="button/CONTINUE", callback_data="return"))
        builder.adjust(1)
        return builder.as_markup()

    def yes_no_keyboard(self, return_button: bool = False) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            self._inline_button(text_key="button/YES", callback_data="yes"),
            self._inline_button(text_key="button/NO", callback_data="no"),
        )
        if return_button:
            builder.add(self.return_button())
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
        builder.button(
            text=loc.get_text("button/AGREE", self._language),
            callback_data="terms_agree",
        )
        builder.button(
            text=loc.get_text("button/DISAGREE", self._language),
            callback_data="terms_disagree",
        )
        builder.adjust(2)
        return builder.as_markup()

    def language_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🇷🇺Русский", callback_data="language ru")
        builder.button(text="🇺🇸English", callback_data="language en")
        builder.adjust(2)
        return builder.as_markup()

    def choose_line_keyboard(self, lines: list[ProdutionLine]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for line in lines:
            builder.button(text=line.name, callback_data=LineCallback(id=line.id).pack())
        builder.adjust(1)
        return builder.as_markup()

    async def operator_buttons(self, line: ProductionLine) -> list[InlineKeyboardButton]:
        return [
            InlineKeyboardButton(text=operator.name, callback_data=f"operator:{operator.id}")
            for operator in await Operator.find(Operator.line_id == line.id).to_list()
        ]

    def choose_action_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/START_SHIFT"),
            callback_data="start_shift",
        )
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def choose_order_keyboard(self, orders: list[Order]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for order in orders:
            builder.button(
                text=order.name,
                callback_data=f"order:{order.id}",
            )

        builder.button(
            text=loc.get_text("button/FINISH_SHIFT"),
            callback_data="finish_shift",
        )
        builder.button(text=loc.get_text("button/IDLE"), callback_data="idle")
        builder.adjust(1)
        return builder.as_markup()

    def choose_bundle_keyboard(self, bundles: list[Bundle]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for bundle in bundles:
            builder.button(
                text=bundle.native_id,
                callback_data=f"bundle:{bundle.id}",
            )

        builder.button(
            text=loc.get_text("button/FINISH_SHIFT"),
            callback_data="finish_shift",
        )
        builder.button(text=loc.get_text("button/IDLE"), callback_data="idle")
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def choose_product_keyboard(self, products: list[Product]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for product in products:
            builder.button(
                text=product.native_id,
                callback_data=f"product:{product.id}",
            )

        builder.button(
            text=loc.get_text("button/FINISH_BUNDLE"),
            callback_data="finish_bundle",
        )
        builder.button(
            text=loc.get_text("button/FINISH_SHIFT"),
            callback_data="finish_shift",
        )
        builder.button(text=loc.get_text("button/IDLE"), callback_data="idle")
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def results_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/10_PRODUCTS"),
            callback_data="10_products",
        )
        builder.button(
            text=loc.get_text("button/OTHER_COUNT"),
            callback_data="input_count",
        )
        builder.button(
            text=loc.get_text("button/FINISH_PRODUCT"),
            callback_data="finish_product",
        )

        builder.button(
            text=loc.get_text("button/FINISH_SHIFT"),
            callback_data="finish_shift",
        )
        builder.button(text=loc.get_text("button/IDLE"), callback_data="idle")
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/SCHEDULED_IDLE"),
            callback_data=IdleType.SCHEDULED,
        )
        builder.button(
            text=loc.get_text("button/UNSCHEDULED_IDLE"),
            callback_data=IdleType.UNSCHEDULED,
        )

        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def scheduled_idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/REPAIR"),
            callback_data=f"idle:{IdleType.SCHEDULED}:{ScheduledIdleReason.REPAIR}",
        )
        builder.button(
            text=loc.get_text("button/NO_ORDERS"),
            callback_data=f"idle:{IdleType.SCHEDULED}:{ScheduledIdleReason.NO_ORDERS}",
        )
        builder.button(
            text=loc.get_text("button/COIL_REPLACE"),
            callback_data=f"idle:{IdleType.SCHEDULED}:{ScheduledIdleReason.COIL_REPLACE}",
        )

        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def unscheduled_idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/BREAKDOWN"),
            callback_data=f"idle:{IdleType.UNSCHEDULED}:{UnscheduledIdleReason.BREAKDOWN}",
        )
        builder.button(
            text=loc.get_text("button/OTHER_REASON"),
            callback_data=f"idle:{IdleType.UNSCHEDULED}:{UnscheduledIdleReason.OTHER}",
        )

        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def finish_idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/FINISH_IDLE"),
            callback_data=f"finish_idle",
        )
        builder.adjust(1)
        return builder.as_markup()

    def admin_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/ADD_OPERATOR"),
            callback_data="add_operator",
        )
        builder.button(
            text=loc.get_text("button/ADD_ACCOUNT"),
            callback_data="add_account",
        )
        builder.adjust(1)
        return builder.as_markup()
