import asyncio
import logging

from oddsapi.database.init import SessionLocal
from oddsapi.database.models import League
from oddsapi.database.repository.bet import get_bet_bookmakers
from oddsapi.database.repository.league import get_leagues_with_fixtures

def get_leagues_str(leagues: list[League]):
    # concatenate bookmaker names and count
    leagues_str = [f"{league.name} - {league.fixture_count}" for league in leagues]
    return leagues_str

def get_leagues(bookmaker: str):
    # return []
    async def async_get_leagues():
        async with SessionLocal() as session:
            data = await get_leagues_with_fixtures(session, bookmaker)
            return data

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop:
        logging.info(
            "Event loop running, skipping async call and using default values for leagues."
        )
        return [""]
    else:
        leagues = asyncio.run(async_get_leagues())

    return leagues


def get_bookmakers():
    # return []
    async def async_get_bookmakers():
        async with SessionLocal() as session:
            data = await get_bet_bookmakers(session)
            return data

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop:
        logging.info(
            "Event loop is already running, skipping async call and using default values for bookmakers."
        )
        return ["fonbet - 0", "marathon - 0", "pinnacle - 0", "betcity - 0"]
    else:
        bookmaker_data = asyncio.run(async_get_bookmakers())

    # concatenate bookmaker names and count
    result = []
    for bookmaker in bookmaker_data:
        result.append(f"{bookmaker[0]} - {bookmaker[1]}")

    return result
