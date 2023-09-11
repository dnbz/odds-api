import asyncio
import json
import logging
from abc import abstractmethod, ABC
from dataclasses import asdict
from enum import IntEnum
from typing import Type, TypeVar

import dateparser
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.data_models import (
    BetcityEvent,
    FonbetEvent,
    MarathonEvent,
    PinnacleEvent,
    CommonEvent,
)
from oddsapi.database.init import SessionLocal
from oddsapi.database.models import Bet
from oddsapi.database.redis_connection import redis_connect, RedisDB
from oddsapi.database.repository.bet import (
    upsert_bet,
)
from oddsapi.database.repository.fixture import find_fixture_ilike, find_fixture_partial
from oddsapi.helpers import configure_logging
from oddsapi.parser_import.convert import (
    convert_object_key_totals,
    convert_object_key_first_half_totals,
)

T = TypeVar("T", bound=BetcityEvent | FonbetEvent | MarathonEvent | PinnacleEvent)


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
    def convert_bet(self, event, event_date, fixture) -> Bet:
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
            print(data[1])
            event = self.event_cls(**json.loads(data[1]))

        return event

    async def check_event(self, event: T) -> bool:
        """Verify that event doesn't have any None values. in fields home_win, draw, away_win"""
        # TODO: adjust this method for different structure
        # if not event.home_team or not event.draw or not event.away_team:
        #     return False

        return True

    async def process_events(self):
        debug_break_count = 0
        while True:
            # limit number of processed items in debug mode
            if self.debug:
                debug_break_count += 1
                if debug_break_count > self.debug_limit:
                    break

            event = await self.get_event()
            if not await self.check_event(event):
                logging.error(
                    f"Event has None values in home_win, draw, away_win fields: {event}"
                )
                continue

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

    async def handle_event(self, event, session: AsyncSession) -> ProcessStatus:
        event_date = dateparser.parse(event.datetime)
        if not event_date:
            logging.warning(f"Couldn't parse date for event: {event}.\nSkipping...")
            return ProcessStatus.DateParseError

        # TODO: this should be properly via some sort of sanitize process
        event.away_team_name = event.away_team_name.replace("(", "")
        event.away_team_name = event.away_team_name.replace(")", "")
        event.home_team_name = event.home_team_name.replace("(", "")
        event.home_team_name = event.home_team_name.replace(")", "")

        fixture = await find_fixture_ilike(
            event.home_team_name, event.away_team_name, event_date, session
        )

        if not fixture:
            logging.debug(
                f"Couldn't find fixture for event {event}. Trying soft search"
            )

            fixture = await find_fixture_partial(
                event.home_team_name, event.away_team_name, event_date, session
            )

            if not fixture:
                logging.warning(
                    f"Couldn't find fixture with soft search for event {event}.\nSkipping..."
                )
                return ProcessStatus.NotFoundError

        # TODO: improve naming/call order to be more understandable
        bet = self.convert_bet(event, event_date, fixture)

        normalized_bet = CommonEvent(**asdict(bet))
        # TODO: fix naming, shouldn't use something more apparent than event_queue
        updated = await upsert_bet(normalized_bet, fixture, self.event_queue, session)
        await session.commit()

        if updated:
            return ProcessStatus.Updated
        else:
            return ProcessStatus.Added

    async def print_stats(self):
        # log stats with timestamp asynchronously every 30 seconds
        while True:
            logging.info(f"Processing stats: {self.stats}")
            await asyncio.sleep(self.stats_interval)

    async def start(self):
        await asyncio.gather(self.process_events(), self.print_stats())


class BetcityListener(ParserListener):
    @property
    def event_cls(self):
        return BetcityEvent

    @property
    def event_queue(self):
        return "betcity"

    def convert_bet(self, event: BetcityEvent, event_date, fixture):
        processed_event = convert_object_key_first_half_totals(event)
        return processed_event


class PinnacleListener(ParserListener):
    @property
    def event_cls(self):
        return PinnacleEvent

    @property
    def event_queue(self):
        return "pinnacle"

    def convert_bet(self, event: PinnacleEvent, event_date, fixture):
        processed_event = convert_object_key_totals(event)
        processed_event = convert_object_key_first_half_totals(processed_event)
        return processed_event


class MarathonListener(ParserListener):
    @property
    def event_cls(self):
        return MarathonEvent

    @property
    def event_queue(self):
        return "marathon"

    def convert_bet(self, event: MarathonEvent, event_date, fixture):
        processed_event = convert_object_key_totals(event)
        processed_event = convert_object_key_first_half_totals(processed_event)
        return processed_event


class FonbetListener(ParserListener):
    @property
    def event_cls(self):
        return FonbetEvent

    @property
    def event_queue(self):
        return "fonbet"

    def convert_bet(self, event: BetcityEvent, event_date, fixture):
        return event
