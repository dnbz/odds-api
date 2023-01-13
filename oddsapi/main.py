import asyncio
import logging

from .db import init_db
from .loaders import (
    load_matches,
)

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


async def async_main():
    await init_db()
    # await load_static()
    await load_matches()


def main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_main())


main()
