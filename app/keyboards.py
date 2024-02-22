import config

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from beanie import PydanticObjectId

from app.models import User, Company, Report, CompanyLink, CompanyEditRequest
from app.enums import ReportReason, CompanyRole
from loaders import loc


class KeyboardCollection:
    def __init__(self, lang: str) -> None:
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

    def get_contact_keyboard(self) -> ReplyKeyboardMarkup:
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