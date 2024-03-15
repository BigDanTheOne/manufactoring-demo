import asyncio
import sys
from pathlib import Path

from beanie import init_beanie
from beanie.operators import Eq

sys.path.insert(1, str(Path(__file__).parent / ".."))

from app.enums import UserRole
from app.models import Account
from loaders import mongo_client


async def create_or_update(phone: str, role: UserRole) -> None:
    account = await Account.find_one(Eq(Account.phone, phone))
    if account is None:
        await Account(phone=phone, role=role).create()
    else:
        account.role = role
        account.save()


async def main(phone: str, role: UserRole) -> None:
    await init_beanie(database=mongo_client.get_database(), document_models=[Account])

    await create_or_update(phone=phone, role=role)


def _phone_validate(phone: str) -> str:
    def _is_decimal(c: str) -> bool:
        _decimal = "0123456789"
        return c in _decimal

    if all(_is_decimal(c) for c in phone) and 11 <= len(phone) <= 13:
        return phone
    raise ValueError("wrong phone number")


def _role_validate(role_str: str) -> UserRole:
    return UserRole(role_str)


def _help() -> None:
    print(
        f"Usage: python {Path(__file__).name} <phone> <role>\n"
        "phone  - phone number in format +79998887766, without leading '+' (11-13 digits)\n"
        f"role   - '{UserRole.OPERATOR}' or '{UserRole.ADMIN}'"
    )


def get_args() -> tuple[str, UserRole]:
    try:
        _, phone, role_str = sys.argv
        phone = _phone_validate(phone)
        role = _role_validate(role_str)
    except ValueError:
        _help()
        exit(1)
    return phone, role


if __name__ == "__main__":
    phone, role = get_args()
    asyncio.run(main(phone=phone, role=role))
