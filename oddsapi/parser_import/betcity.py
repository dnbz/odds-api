import logging

import dateparser
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.data_models import BetcityEvent
from oddsapi.database.repository.bet import upsert_betcity_bet
from oddsapi.database.repository.fixture import find_fixture_ilike, find_fixture_partial
from oddsapi.parser_import.base import ParserListener, ProcessStatus


class BetcityListener(ParserListener):
    @property
    def event_cls(self):
        return BetcityEvent

    @property
    def event_queue(self):
        return "betcity"

    async def handle_event(
        self, event: BetcityEvent, session: AsyncSession
    ) -> ProcessStatus:
        event_date = dateparser.parse(event.datetime)
        if not event_date:
            logging.warning(f"Couldn't parse date for event: {event}.\nSkipping...")
            return ProcessStatus.DateParseError

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

        updated = await upsert_betcity_bet(event, event_date, fixture, session)
        await session.commit()

        if updated:
            return ProcessStatus.Updated
        else:
            return ProcessStatus.Added
