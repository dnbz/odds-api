import asyncio
import binascii
import io
from datetime import timedelta
from enum import Enum, IntEnum

from PIL import Image
from plotly import graph_objects as go
from tortoise import Tortoise

from .settings import (
    TORTOISE_ORM_CONFIG,
    APP_ENV,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
)

import redis.asyncio as redis


class RedisDB(IntEnum):
    WORKER_QUEUE = 0
    MAIN_CACHE = 1
    BETCITY = 2


async def init_db():
    await Tortoise.init(TORTOISE_ORM_CONFIG)
    # Generate the schema
    await Tortoise.generate_schemas()


def redis_connect(db=RedisDB.MAIN_CACHE):
    # for some reason I get ResponseError when connecting without str()
    # number literal works fine however
    db = str(db)

    if APP_ENV == "dev":
        host = "127.0.0.1"
    else:
        host = REDIS_HOST

    connection = redis.Redis(
        host=host, password=REDIS_PASSWORD, port=REDIS_PORT, db=db
    )

    return connection
