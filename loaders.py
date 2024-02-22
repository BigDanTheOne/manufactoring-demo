import os
import config
import logging

from redis.asyncio.client import Redis
from motor.motor_asyncio import AsyncIOMotorClient

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.client.session.aiohttp import AiohttpSession

from app.extras.localizator import Localizator


redis_client = Redis(
    db=config.REDIS_DB,
    host=config.REDIS_HOST,
    port=int(config.REDIS_PORT),
)
storage_key = DefaultKeyBuilder(prefix=config.REDIS_PREFIX)
storage = RedisStorage(redis=redis_client, key_builder=storage_key)
mongo_client = AsyncIOMotorClient(config.MONGODB_CONN)
dp = Dispatcher(storage=storage)
aiosession = AiohttpSession()
bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML", session=aiosession)
loc = Localizator("data/texts.csv")
