import os
from dotenv import load_dotenv
from typing import cast, TypedDict


load_dotenv(override=True)


# Bot config
BOT_TOKEN = cast(str, os.getenv("BOT_TOKEN"))
BOT_LINK = cast(str, os.getenv("BOT_LINK"))

BOT_ALIVE = cast(str, os.getenv("BOT_ALIVE"))
BOT_ALIVE = True if BOT_ALIVE == "1" else False

DEBUG_MODE = cast(str, os.getenv("DEBUG_MODE"))
DEBUG_MODE = True if DEBUG_MODE == "1" else False


# redis config
REDIS_HOST = cast(str, os.getenv("REDIS_HOST"))
REDIS_DB = cast(str, os.getenv("REDIS_DB"))
REDIS_PORT = cast(str, os.getenv("REDIS_PORT"))
REDIS_PREFIX = cast(str, os.getenv("REDIS_PREFIX"))


# mongo config
MONGODB_CONN = os.getenv("MONGODB_CONN")


SPECIFIC_GRAVITY = 0.00785
