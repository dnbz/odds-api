import datetime

from arq import cron
from arq.connections import RedisSettings

from oddsapi.database.redis_connection import RedisDB
from oddsapi.helpers import time_now, configure_logging
from oddsapi.tgbot.tgbot import run_tg_notify
from httpx import AsyncClient

from oddsapi.apifootball.loader import load_matches, load_static
from oddsapi.settings import REDIS_PASSWORD, REDIS_HOST


def get_redis_settings() -> RedisSettings:
    return RedisSettings(
        password=REDIS_PASSWORD, database=RedisDB.WORKER_QUEUE, host=REDIS_HOST
    )


async def download_content(ctx, url):
    session: AsyncClient = ctx["session"]
    response = await session.get(url)
    print(f"{url}: {response.text:.80}...")
    return len(response.text)


async def startup(ctx):
    configure_logging()


async def shutdown(ctx):
    pass


async def notify(ctx):
    await run_tg_notify()


async def update_static(ctx):
    await load_static(delete=False)


async def update_matches(ctx):
    await load_matches(delete=False)


def get_min_sec():
    time = time_now()
    interval = datetime.timedelta(seconds=20)
    target_time = time + interval

    return {
        "hour": target_time.hour,
        "minute": target_time.minute,
        "second": target_time.second,
    }


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli.
# For a list of available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()

    # debug run time
    # debug_time = get_min_sec()
    cron_jobs = [
        cron(update_static, hour={22}, minute=15),
        # cron(update_static, **debug_time),
        # odd hours
        cron(update_matches, hour={hour for hour in range(1, 24, 2)}, minute=35),
        # every 10 min.
        cron(notify, hour=None, minute={minute for minute in range(1, 60, 10)}),
    ]
