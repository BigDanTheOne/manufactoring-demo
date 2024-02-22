import os
import asyncio
import logging
import config

from beanie import init_beanie

from app.middlewares import AlbumMiddleware, UserMiddleware
from app.handlers import (
    bot_sleep,
    global_commands_handlers,
)
from app.models import (
    User
)
from loaders import mongo_client, bot, dp


async def main():
    await init_beanie(
        database=mongo_client.get_database(),
        document_models=[
            User,
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
        dp.include_routers(
            global_commands_handlers.router,
        )
    else:
        dp.include_routers(bot_sleep.router)

    dp.message.middleware(AlbumMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
