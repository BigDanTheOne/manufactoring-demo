import config

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from beanie import PydanticObjectId

from app.models import User, Employee, Order, Bundle
from app.enums import IdleType
from loaders import loc


class KeyboardCollection:
    def __init__(self, lang: str = "ru") -> None:
        self._language = lang

    def return_button(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=loc.get_text("button/RETURN", self._language),
            callback_data="return",
        )

    def return_button_row(self) -> list[list[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(
                    text=loc.get_text("button/RETURN", self._language),
                    callback_data="return",
                )
            ]
        ]

    def return_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def yes_no_keyboard(
        self, return_button: bool = False
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/YES", self._language),
            callback_data="yes",
        )
        builder.button(
            text=loc.get_text("button/NO", self._language), callback_data="no"
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

    async def employee_buttons(self) -> list[InlineKeyboardButton]:
        return [
            InlineKeyboardButton(
                text=employee.name, callback_data=f"employee:{employee.id}"
            )
            for employee in await Employee.all().to_list()
        ]

    def choose_action_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/START_SHIFT"),
            callback_data="start_shift",
        )
        builder.button(
            text=loc.get_text("button/RETURN"), callback_data="return"
        )
        builder.adjust(1)
        return builder.as_markup()

    def choose_order_keyboard(
        self, orders: list[Order]
    ) -> InlineKeyboardMarkup:
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

    def choose_bundle_keyboard(
        self, bundles: list[Bundle]
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for bundle in bundles:
            builder.button(
                text=bundle.id,
                callback_data=f"bundle:{bundle.id}",
            )

        builder.button(
            text=loc.get_text("button/FINISH_SHIFT"),
            callback_data="finish_shift",
        )
        builder.button(text=loc.get_text("button/IDLE"), callback_data="idle")
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
            text=loc.get_text("button/FINISH_BUNDLE"),
            callback_data="finish_bundle",
        )

        builder.button(
            text=loc.get_text("button/FINISH_SHIFT"),
            callback_data="finish_shift",
        )
        builder.button(text=loc.get_text("button/IDLE"), callback_data="idle")
        builder.adjust(1)
        return builder.as_markup()

    def idle_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.button(
            text=loc.get_text("button/SCHEDULED_FINISH"),
            callback_data=IdleType.SCHEDULED,
        )
        builder.button(
            text=loc.get_text("button/UNSCHEDULED_FINISH"),
            callback_data=IdleType.UNSCHEDULED,
        )

        builder.button(
            text=loc.get_text("button/RETURN"), callback_data="return"
        )
        builder.adjust(1)
        return builder.as_markup()
