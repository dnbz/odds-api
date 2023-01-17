import asyncio
import datetime

from arq import create_pool, cron
from arq.connections import RedisSettings

from oddsapi.db import RedisDB, init_db
from .api_client import get_httpx_config
from .helpers import time_now, configure_logging
from .tg import notify as tg_notify
from httpx import AsyncClient

from .loaders import (
    load_static,
    load_matches,
)
from .settings import REDIS_PASSWORD


def get_redis_settings() -> RedisSettings:
    return RedisSettings(password=REDIS_PASSWORD, database=RedisDB.WORKER_QUEUE)


async def download_content(ctx, url):
    session: AsyncClient = ctx["session"]
    response = await session.get(url)
    print(f"{url}: {response.text:.80}...")
    return len(response.text)


async def startup(ctx):
    await init_db()
    configure_logging()
    ctx["session"] = AsyncClient(**get_httpx_config())


async def shutdown(ctx):
    await ctx["session"].aclose()


async def notify(ctx):
    await tg_notify()


async def update_static(ctx):
    await load_static(delete=False)


async def update_matches(ctx):
    await load_matches(delete=False)


def get_min_sec():
    time = time_now()
    interval = datetime.timedelta(seconds=20)
    target_time = time + interval

    return target_time.minute, target_time.second


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli.
# For a list of available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()

    # debug run time
    # min, sec = get_min_sec()
    cron_jobs = [
        cron(update_static, hour={22}, minute=15),
        # odd hours
        cron(update_matches, hour={hour for hour in range(1, 24, 2)}, minute=35),
        # every 10 min.
        cron(notify, hour=None, minute={minute for minute in range(1, 60, 10)}),
    ]
