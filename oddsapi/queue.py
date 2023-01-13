import asyncio

from arq import create_pool, cron
from arq.connections import RedisSettings

from oddsapi.db import RedisDB
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
    ctx["session"] = AsyncClient()


async def shutdown(ctx):
    await ctx["session"].aclose()


async def notify(ctx):
    await tg_notify()


async def update_static(ctx):
    await load_static(delete=False)


async def update_matches(ctx):
    await load_matches(delete=False)


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli.
# For a list of available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()

    cron_jobs = [
        cron(update_static, hour={22}, minute=15),
        # odd hours
        cron(update_matches, hour={hour for hour in range(1, 24, 2)}, minute=35),
        # every 10 min.
        cron(notify, hour=None, minute={minute for minute in range(1, 60, 10)}),
    ]


if __name__ == "__main__":
    pass
    # asyncio.run(main())
