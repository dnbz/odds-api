import asyncio
import json
import logging
import re
import time
import traceback

from datetime import datetime
from enum import IntEnum
from pprint import pprint
from string import Template

import dateparser
import tortoise
from psycopg2.extensions import adapt

from redis.asyncio import Redis
from tortoise import connections

from oddsapi.db import redis_connect, RedisDB, init_db
from oddsapi.db_import import add_betcity_bet, BetcityEvent
from oddsapi.helpers import configure_logging
from oddsapi.models import Fixture


class ProcessStatus(IntEnum):
    Added = 0
    Updated = 1
    NotFoundError = 2
    DateParseError = 3


async def reader(client: Redis):
    stats = {
        "added": 0,
        "updated": 0,
        "errors": {
            "not_found": 0,
            "dateparse_error": 0,
        },
    }

    count = 0
    while True:
        # while count < 800:
        event = await get_event(client)
        status = await process_event(event)

        if status == ProcessStatus.Added:
            stats["added"] += 1
        elif status == ProcessStatus.Updated:
            stats["updated"] += 1
        elif status.NotFoundError:
            stats["errors"]["not_found"] += 1
        elif status.DateParseError:
            stats["errors"]["dateparse_error"] += 1

        count += 1

    logging.info(f"Processing stats: {stats}")


async def process_event(event: BetcityEvent) -> ProcessStatus:
    logging.info(f"Processing event {event}")

    event_date = dateparser.parse(event.datetime)
    if not event_date:
        logging.warning(f"Couldn't parse date for event: {event}.\nSkipping...")
        return ProcessStatus.DateParseError

    fixture = await find_fixture_ilike(
        event.home_team_name, event.away_team_name, event_date
    )
    if not fixture:
        logging.debug(f"Couldn't find fixture for event {event}. Trying soft search")

        fixture = await find_fixture_soft(
            event.home_team_name, event.away_team_name, event_date
        )

        if not fixture:
            logging.warning(
                f"Couldn't find fixture with soft search for event {event}.\nSkipping..."
            )
            return ProcessStatus.NotFoundError

    updated = await add_betcity_bet(event, event_date, fixture)

    if updated:
        return ProcessStatus.Updated
    else:
        return ProcessStatus.Added


async def get_event(client: Redis) -> BetcityEvent:
    queue = "betcity"
    data = await client.brpop([queue])
    # data = await client.blmove(
    #     "betcity", "betcity", timeout=0, src="RIGHT", dest="LEFT"
    # )

    # event = BetcityEvent(**json.loads(data))
    event = BetcityEvent(**json.loads(data[1]))
    return event


async def find_fixture_ilike(
    home_team: str, away_team: str, date: datetime
) -> Fixture | None:
    date = date.strftime("%Y-%m-%d")
    sql = Template(
        """
    select * from fixture where unaccent(home_team_name) ilike $home_team
    and unaccent(away_team_name) ilike $away_team
    and date > NOW()
    and date >= $date::date and date < ($date::date + interval '1 day')
    """
    ).substitute(
        {
            "home_team": sanitize(f"%{home_team}%"),
            "away_team": sanitize(f"%{away_team}%"),
            "date": sanitize(date),
        }
    )
    logging.log(5, f"Running sql {sql}")

    try:
        fixtures = await Fixture.raw(sql)
    except tortoise.exceptions.OperationalError:
        logging.error(f"An error occurred while running this sql {sql}")
        raise

    logging.log(5, f"Found fixtures {fixtures}")

    if len(fixtures) > 0:
        return fixtures[0]


async def find_fixture_soft(
    home_team: str, away_team: str, date: datetime
) -> Fixture | None:
    """Finds a fixture if any of the words in the team name match"""

    home_team = prepate_text(home_team)
    away_team = prepate_text(away_team)

    date = date.strftime("%Y-%m-%d")
    sql = Template(
        """
    select * from fixture where unaccent(home_team_name) similar to $home_team
    and unaccent(away_team_name) similar to $away_team
    and date > NOW()
    and date >= $date::date and date < ($date::date + interval '1 day')
    """
    ).substitute(
        {"home_team": home_team, "away_team": away_team, "date": sanitize(date)}
    )
    logging.log(5, f"Running sql {sql}")

    try:
        fixtures = await Fixture.raw(sql)
    except tortoise.exceptions.OperationalError:
        logging.error(f"An error occurred while running this sql {sql}")
        raise

    logging.log(5, f"Found fixtures {fixtures}")

    if len(fixtures) > 0:
        return fixtures[0]


def prepate_text(text: str) -> str:
    """Convert text to sql query for search.
    Adds | between words and discards words < 3 chars long"""

    # remove whitespace
    text = re.sub(r"\s+", " ", text.strip())
    # dashes are sometimes used in place of spaces
    text = text.replace("-", " ")

    words = text.split(" ")

    if len(words) < 2:
        result = sanitize(f"%{words[0]}%")

    words = [word for word in words if len(word) > 3]

    result = "|".join(words)

    return sanitize(f"%({result})%")


def sanitize(string: str) -> str:
    try:
        qs = adapt(string)
        return str(qs)
    except UnicodeEncodeError:
        logging.warning(f"Couldn't encode string {string}")
        traceback.print_exc()

        qs = adapt(string)
        qs.encoding = "utf-8"
        return str(qs)

        # It's odd that psycopg2 even uses latin-1


def betcity_main():
    async def run():
        await init_db()

        conn = connections.get("default")
        await conn.execute_query("CREATE EXTENSION IF NOT EXISTS unaccent")

        client = await redis_connect(RedisDB.BETCITY)

        await reader(client)
        await client.close()

    asyncio.run(run())