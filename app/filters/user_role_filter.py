from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.models import Account


class UserRoleFilter(BaseFilter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        user = await Account.by_tg_id(obj.from_user.id)
        if user is None:
            return False
        return user.role == self.role
