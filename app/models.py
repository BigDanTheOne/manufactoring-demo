from __future__ import annotations

import os
import logging
from datetime import datetime

from beanie import Document, PydanticObjectId
from beanie.operators import In, RegEx
from aiogram.types import BufferedInputFile

from app.enums import UserRole, CompanyRole
from loaders import bot, ips_api


class User(Document):
    tg_id: int
    tg_username: str | None
    name: str
    phone: str
    reg_date: datetime
    role: str = UserRole.USER
    language: str
