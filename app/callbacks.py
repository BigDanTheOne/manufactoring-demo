from aiogram.filters.callback_data import CallbackData
from beanie import PydanticObjectId

from app.enums import IdleReason, IdleType


class FinishProducts(CallbackData, prefix="finish_products"):
    quantity: int


class Line(CallbackData, prefix="line"):
    id: PydanticObjectId


class Operator(CallbackData, prefix="operator"):
    id: PydanticObjectId


class Order(CallbackData, prefix="order"):
    id: PydanticObjectId


class Bundle(CallbackData, prefix="bundle"):
    id: PydanticObjectId


class Product(CallbackData, prefix="product"):
    id: PydanticObjectId


class Idle(CallbackData, prefix="idle"):
    type: IdleType


class IdleOption(CallbackData, prefix="idle"):
    type: IdleType
    reason: IdleReason
