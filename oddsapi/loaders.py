import asyncio
import datetime
import logging

import httpx
from httpx import AsyncClient

from .api_client import (
    get_teams_by_country,
    get_rapidapi_headers,
    get_countries,
    get_leagues,
    get_bookmakers,
    get_fixtures_by_date,
    get_bets_pagination,
    get_bets_by_date,
    get_httpx_proxy,
    get_httpx_config,
)
from .db_import import (
    add_team,
    add_country,
    add_league,
    add_bookmaker,
    add_fixture,
    add_bet,
)
from .models import Team, Country, League, Bookmaker, Fixture, Bet
from .settings import BOOKMAKERS, BET_PARSE_DAYS, FIXTURE_PARSE_DAYS


# load data in strict order
async def init_load(delete=False):
    await load_leagues(delete=delete)
    await load_countries(delete=delete)
    await load_bookmakers(delete=delete)
    await load_teams(delete=delete)
    await load_fixtures(delete=delete)
    await load_bets(delete=delete)


# load data in strict order
async def load_static(delete=False):
    await load_leagues(delete=delete)
    await load_countries(delete=delete)
    await load_bookmakers(delete=delete)
    await load_teams(delete=delete)


async def load_matches(delete=False):
    await load_fixtures(delete=delete)
    await load_bets(delete=delete)


async def load_bets_by_bookmaker(data: dict):
    bookmakers = [
        bookmaker for bookmaker in data["bookmakers"] if bookmaker["name"] in BOOKMAKERS
    ]
    add_bet_coros = [add_bet(data, bookmaker) for bookmaker in bookmakers]

    await asyncio.gather(*add_bet_coros)


async def load_bets_by_page(client: AsyncClient, date, page):
    bets = await get_bets_by_date(client, date, page)
    load_bets_by_bookmaker_coros = [load_bets_by_bookmaker(bet) for bet in bets]

    await asyncio.gather(*load_bets_by_bookmaker_coros)


async def load_bets_by_date(client: AsyncClient, date):
    pages = await get_bets_pagination(client, date)

    load_bets_by_page_coros = [
        load_bets_by_page(client, date, page) for page in range(1, pages + 1)
    ]
    await asyncio.gather(*load_bets_by_page_coros)


async def load_bets(delete=False):
    if delete:
        logging.info("Delete flag passed. Deleting existing bets...")
        await Bet.all().delete()

    day = datetime.timedelta(days=1)
    date_now = datetime.datetime.now()
    days = BET_PARSE_DAYS
    dates = [(date_now + day * i).strftime("%Y-%m-%d") for i in range(days)]

    async with httpx.AsyncClient(**get_httpx_config()) as client:
        load_bets_by_date_coros = [load_bets_by_date(client, date) for date in dates]
        await asyncio.gather(*load_bets_by_date_coros)


async def load_fixtures_by_date(client: AsyncClient, date):
    fixtures = await get_fixtures_by_date(client, date)

    add_fixture_coros = [add_fixture(fixture) for fixture in fixtures]
    logging.info(f"Adding {len(add_fixture_coros)} fixtures for date {date}")

    await asyncio.gather(*add_fixture_coros)


async def load_fixtures(delete=False):
    if delete:
        logging.info("Delete flag passed. Deleting existing fixtures...")
        await Fixture.all().delete()

    day = datetime.timedelta(days=1)
    date_now = datetime.datetime.now()
    days = FIXTURE_PARSE_DAYS
    dates = [(date_now + day * i).strftime("%Y-%m-%d") for i in range(days)]

    async with httpx.AsyncClient(**get_httpx_config()) as client:
        load_fixtures_by_date_coros = [
            load_fixtures_by_date(client, date) for date in dates
        ]
        await asyncio.gather(*load_fixtures_by_date_coros)


async def load_bookmakers(delete=False):
    async with httpx.AsyncClient(**get_httpx_config()) as client:
        bookmakers = await get_bookmakers(client)

    if delete:
        logging.info("Delete flag passed. Deleting existing bookmakers...")
        await Bookmaker.all().delete()

    add_bookmaker_coros = [add_bookmaker(bookmaker) for bookmaker in bookmakers]
    bookmaker_count = len(add_bookmaker_coros)

    await asyncio.gather(*add_bookmaker_coros)
    logging.info(f"Imported {bookmaker_count} bookmakers.")


async def load_teams_by_country(client: AsyncClient, country):
    teams = await get_teams_by_country(client, country.name)
    add_team_coros = [add_team(team, country.id) for team in teams]

    await asyncio.gather(*add_team_coros)


async def load_teams(delete=False):
    if delete:
        logging.info("Delete flag passed. Deleting existing teams...")
        await Team.all().delete()

    countries = await Country.all().only("id", "name")
    if not countries:
        logging.warning("No countries found. Can't import teams...")

    async with httpx.AsyncClient(**get_httpx_config()) as client:
        load_teams_by_country_coros = [
            load_teams_by_country(client, country=country) for country in countries
        ]
        await asyncio.gather(*load_teams_by_country_coros)


async def load_countries(delete=False):
    if delete:
        logging.info("Delete flag passed. Deleting existing countries...")
        await Country.all().delete()

    async with httpx.AsyncClient(**get_httpx_config()) as client:
        countries = await get_countries(client)

    add_country_coros = [add_country(country) for country in countries]
    country_count = len(add_country_coros)

    await asyncio.gather(*add_country_coros)
    logging.info(f"Imported {country_count} countries.")


async def load_leagues(delete=False):
    if delete:
        logging.info("Delete flag passed. Deleting existing leagues...")
        await League.all().delete()

    async with httpx.AsyncClient(**get_httpx_config()) as client:
        leagues = await get_leagues(client)

    add_league_coros = [add_league(league) for league in leagues]
    league_count = len(add_league_coros)

    await asyncio.gather(*add_league_coros)

    logging.info(f"Imported {league_count} leagues.")
