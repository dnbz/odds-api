import asyncio
import json
import logging
from abc import abstractmethod, ABC
from enum import IntEnum
from typing import Type, TypeVar

import dateparser
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.data_models import BetcityEvent, FonbetEvent
from oddsapi.database.init import SessionLocal
from oddsapi.database.redis_connection import redis_connect, RedisDB
from oddsapi.database.repository.bet import upsert_betcity_bet
from oddsapi.database.repository.fixture import find_fixture_ilike, find_fixture_partial
from oddsapi.helpers import configure_logging

T = TypeVar("T", bound=BetcityEvent | FonbetEvent)


class ProcessStatus(IntEnum):
    Added = 0
    Updated = 1
    NotFoundError = 2
    DateParseError = 3


class ParserListener(ABC):
    stats = {
        "total_events": 0,
        "added": 0,
        "updated": 0,
        "errors": {
            "not_found": 0,
            "dateparse_error": 0,
        },
    }

    debug_limit = 50

    stats_interval = 30

    def __init__(self, debug: bool = False):
        self.debug = debug

        self.redis = redis_connect(RedisDB.PARSERS)
        self.session = SessionLocal()

    @property
    @abstractmethod
    def event_cls(self):
        pass

    @property
    @abstractmethod
    def event_queue(self) -> str:
        pass

    @abstractmethod
    async def handle_event(self, event: T, session: AsyncSession) -> ProcessStatus:
        pass

    async def get_event(self) -> T:
        # append event to the same queue in debug mode
        if self.debug:
            data = await self.redis.blmove(
                self.event_queue, self.event_queue, timeout=0, src="RIGHT", dest="LEFT"
            )

            event = self.event_cls(**json.loads(data))
        else:
            data = await self.redis.brpop([self.event_queue])
            event = self.event_cls(**json.loads(data[1]))

        return event

    async def process_events(self):
        debug_break_count = 0
        while True:
            # limit number of processed items in debug mode
            if self.debug:
                debug_break_count += 1
                if debug_break_count > self.debug_limit:
                    break

            event = await self.get_event()

            logging.info(f"Processing event {event}")

            status = await self.handle_event(event, self.session)

            self.stats["total_events"] += 1

            if status == ProcessStatus.Added:
                self.stats["added"] += 1
            elif status == ProcessStatus.Updated:
                self.stats["updated"] += 1
            elif status.NotFoundError:
                self.stats["errors"]["not_found"] += 1
            elif status.DateParseError:
                self.stats["errors"]["dateparse_error"] += 1

    async def print_stats(self):
        # log stats with timestamp asynchronously every 30 seconds
        while True:
            logging.info(f"Processing stats: {self.stats}")
            await asyncio.sleep(self.stats_interval)

    async def start(self):
        await asyncio.gather(self.process_events(), self.print_stats())
