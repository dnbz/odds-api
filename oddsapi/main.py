import asyncio
import logging
from typing import Callable

from .db import init_db
from .tg import async_main as run_tgbot
from .loaders import (
    load_matches,
    load_static,
)

def configure_logging():
    logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)

configure_logging()


def async_run(func: Callable):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(func())


async def import_matches():
    await init_db()
    # await load_static()
    await load_matches()


async def import_static():
    await init_db()
    await load_static()
    # await load_matches()


def main():
    async_run(import_matches)


def run_import_static():
    async_run(import_static)


def tgbot():
    async_run(run_tgbot)
