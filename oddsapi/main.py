import asyncio
from typing import Callable

from .helpers import configure_logging

from .db import init_db
from .loaders import (
    load_matches,
    load_static,
)

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