from enum import IntEnum

from redis import asyncio as redis  # noqa
from redis.asyncio import Redis  # noqa

from oddsapi.settings import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT


class RedisDB(IntEnum):
    WORKER_QUEUE = 0
    MAIN_CACHE = 1
    PARSERS = 2


def redis_connect(db=RedisDB.MAIN_CACHE) -> Redis:
    # for some reason I get ResponseError when connecting without str()
    # number literal works fine however
    db = str(db)

    host = REDIS_HOST

    connection = redis.Redis(host=host, password=REDIS_PASSWORD, port=REDIS_PORT, db=db)

    return connection
