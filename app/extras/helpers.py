import logging
from aiogram.types import InaccessibleMessage, Message


def get_pure_phone(raw: str) -> str:
    ban_symbols = ["+", "(", ")", "-", " "]
    for symbol in ban_symbols:
        raw = raw.replace(symbol, "")
    if raw[0] == "8":
        raw = "7" + raw[1 : len(raw)]
    return raw


def plural(value: int, variants: list) -> str:
    value = abs(value)
    if value % 10 == 1 and value % 100 != 11:
        variant = 0
    elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
        variant = 1
    else:
        variant = 2
    return variants[variant]


async def try_delete_message(message: Message | InaccessibleMessage | None) -> None:
    if not isinstance(message, Message):
        return
    try:
        await message.delete()
    except Exception:
        logging.info("Message Can't Be Deleted. Passed.")


def is_int(n: str) -> bool:
    try:
        float_n = float(n)
        int_n = int(float_n)
    except ValueError:
        return False
    else:
        return float_n == int_n


def is_float(n: str) -> bool:
    try:
        float_n = float(n)
    except ValueError:
        return False
    else:
        return True
