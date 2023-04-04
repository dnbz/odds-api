import datetime
import logging
from contextlib import asynccontextmanager

import httpx

from oddsapi.apifootball.apiclient import (
    get_bets_by_date,
    get_bets_pagination,
    get_httpx_config,
    get_teams_by_country,
    get_leagues,
    get_countries,
    get_bookmakers,
    get_fixtures_by_date,
)
from oddsapi.database.init import SessionLocal
from oddsapi.database.repository.bet import delete_all_bets, upsert_apifootball_bet
from oddsapi.database.repository.bookmaker import (
    upsert_bookmaker,
    delete_all_bookmakers,
)
from oddsapi.database.repository.country import (
    find_all_countries,
    delete_all_countries,
    upsert_country,
)
from oddsapi.database.repository.fixture import delete_all_fixtures, upsert_fixture
from oddsapi.database.repository.league import delete_all_leagues, upsert_league
from oddsapi.database.repository.team import upsert_team, delete_all_teams
from oddsapi.settings import (
    BOOKMAKERS,
    FIXTURE_PARSE_DAYS,
    BET_PARSE_DAYS,
    DISABLE_PROXY,
)


class ApiFootballLoader:
    def __init__(self, session, client):
        self.session = session
        self.client = client

    async def load_bets(self, delete=False):
        if delete:
            logging.info("Delete flag passed. Deleting existing bets...")
            await delete_all_bets(self.session)

        day = datetime.timedelta(days=1)
        date_now = datetime.datetime.now()
        days = BET_PARSE_DAYS
        dates = [(date_now + day * i).strftime("%Y-%m-%d") for i in range(days)]

        for date in dates:
            pages = await get_bets_pagination(self.client, date)
            for page in range(1, pages + 1):
                bets = await get_bets_by_date(self.client, date, page)
                for bet in bets:
                    bookmakers = [
                        bookmaker
                        for bookmaker in bet["bookmakers"]
                        if bookmaker["name"] in BOOKMAKERS
                    ]
                    for bookmaker in bookmakers:
                        await upsert_apifootball_bet(bet, bookmaker, self.session)

        await self.session.commit()

    async def load_fixtures(self, delete=False):
        if delete:
            logging.info("Delete flag passed. Deleting existing fixtures...")
            await delete_all_fixtures(self.session)

        day = datetime.timedelta(days=1)
        date_now = datetime.datetime.now()
        days = FIXTURE_PARSE_DAYS
        dates = [(date_now + day * i).strftime("%Y-%m-%d") for i in range(days)]

        for date in dates:
            fixtures = await get_fixtures_by_date(self.client, date)
            for fixture in fixtures:
                await upsert_fixture(fixture, self.session)

        await self.session.commit()

    async def load_bookmakers(self, delete=False):
        bookmakers = await get_bookmakers(self.client)

        if delete:
            logging.info("Delete flag passed. Deleting existing bookmakers...")
            await delete_all_bookmakers(self.session)

        bookmaker_count = 0
        for bookmaker in bookmakers:
            await upsert_bookmaker(bookmaker, self.session)
            bookmaker_count += 1

        await self.session.commit()

        logging.info(f"Imported {bookmaker_count} bookmakers.")

    async def load_teams(self, delete=False):
        if delete:
            logging.info("Delete flag passed. Deleting existing teams...")
            await delete_all_teams(self.session)

        countries = await find_all_countries(self.session)
        if not countries:
            logging.warning("No countries found. Can't import teams...")

        for country in countries:
            teams = await get_teams_by_country(self.client, country.name)
            for team in teams:
                await upsert_team(team, country.id, self.session)

        await self.session.commit()

    async def load_countries(self, delete=False):
        if delete:
            logging.info("Delete flag passed. Deleting existing countries...")
            await delete_all_countries(self.session)

        countries = await get_countries(self.client)

        country_count = 0
        for country in countries:
            await upsert_country(country, self.session)
            country_count += 1

        await self.session.commit()

        logging.info(f"Imported {country_count} countries.")

    async def load_leagues(self, delete=False):
        if delete:
            logging.info("Delete flag passed. Deleting existing leagues...")
            await delete_all_leagues(self.session)

        leagues = await get_leagues(self.client)

        league_count = 0
        for league in leagues:
            await upsert_league(league, self.session)
            league_count += 1

        await self.session.commit()

        logging.info(f"Imported {league_count} leagues.")


@asynccontextmanager
async def apifootball_context():
    httpx_conf = get_httpx_config(disable_proxy=DISABLE_PROXY)
    async with SessionLocal() as session, httpx.AsyncClient(**httpx_conf) as client:
        yield ApiFootballLoader(session, client)


async def load_matches(delete=False):
    async with apifootball_context() as loader:  # type: ApiFootballLoader
        await loader.load_fixtures(delete)
        # await loader.load_bets(delete)


async def load_static(delete=False):
    async with apifootball_context() as loader:  # type: ApiFootballLoader
        await loader.load_leagues(delete)
        await loader.load_countries(delete)
        await loader.load_bookmakers(delete)
        await loader.load_teams(delete)
