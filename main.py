import os
import asyncio
import logging
import config

from beanie import init_beanie

from app.middlewares import AlbumMiddleware
from app.handlers import bot_sleep, start, operator, admin
from app.models import (
    Account,
    Operator,
    ProdutionLine,
    Plan,
    Order,
    Bundle,
    Product,
)
from loaders import mongo_client, bot, dp


async def run():
    await init_beanie(
        database=mongo_client.get_database(),
        document_models=[
            Account,
            Operator,
            ProdutionLine,
            Plan,
            Order,
            Bundle,
            Product,
        ],
    )

    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging_mode = logging.DEBUG if config.DEBUG_MODE else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)s => %(message)s",
        level=logging_mode,
        datefmt="[%Y-%m-%d %H:%M:%S]",
        handlers=[
            logging.FileHandler("logs/bot.txt"),
            logging.StreamHandler(),
        ],
    )

    logging.info(f"DEBUG_MODE: {config.DEBUG_MODE}")
    logging.info(f"BOT_ALIVE: {config.BOT_ALIVE}")

    if config.BOT_ALIVE:
        dp.include_routers(start.router, operator.router, admin.router)
    else:
        dp.include_routers(bot_sleep.router)

    dp.message.middleware(AlbumMiddleware())

    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
