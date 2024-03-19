from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.models import Account


class UserRoleFilter(BaseFilter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        return (
            obj.from_user is not None and
            (user := await Account.by_tg_id(obj.from_user.id)) is not None
            and user.role == self.role
        )
