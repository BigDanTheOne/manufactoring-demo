import logging
from aiogram.types import Message
from loaders import bot


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


async def try_delete_message(
    message_object_or_id: Message | int, chat_id: int | None = None
) -> None:
    try:
        if isinstance(message_object_or_id, int):
            if chat_id is None:
                raise ValueError("chat_id is None!")
            await bot.delete_message(chat_id, message_object_or_id)
            return
        await message_object_or_id.delete()
    except Exception:
        logging.info("Message Can't Be Deleted. Passed.")
