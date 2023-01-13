import asyncio
import logging

from httpx import AsyncClient

from .settings import API_URL, API_KEY, API_HOST


def get_api_url(path: str) -> str:
    return f"{API_URL}{path}"


def get_rapidapi_headers() -> dict:
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": API_HOST}

    return headers


async def gather_with_concurrency(n, *coros):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


async def get_leagues(client: AsyncClient):
    url = get_api_url("/leagues")

    r = await client.get(url)

    data = r.json()

    logging.info(f"Got leagues. Status: {r.status_code}. Data: {r.text[:45]}")
    return data.get("response")


async def get_countries(client: AsyncClient):
    url = get_api_url("/countries")

    r = await client.get(url)

    data = r.json()

    logging.info(f"Got countries. Status: {r.status_code}. Data: {r.text[:45]}")
    return data.get("response")


async def get_teams_by_country(client: AsyncClient, country: str):
    url = get_api_url("/teams")

    params = {"country": country}

    r = await client.get(url, params=params)

    data = r.json()

    logging.info(f"Got teams. Status: {r.status_code}. Data: {r.text[:45]}")
    return data.get("response")


async def get_bookmakers(client: AsyncClient):
    url = get_api_url("/odds/bookmakers")

    r = await client.get(url)

    data = r.json()

    logging.info(f"Got bookmakers. Status: {r.status_code}. Data: {r.text[:45]}")
    return data.get("response")


async def get_fixtures_by_date(client: AsyncClient, date):
    url = get_api_url("/fixtures")
    params = {
        "date": date,
    }

    r = await client.get(url, params=params)
    data = r.json()

    logging.info(f"Got fixtures. Status: {r.status_code}. Data: {r.text[:45]}")
    return data.get("response")


async def get_bets_by_date(client: AsyncClient, date, page: int = 1):
    url = get_api_url("/odds")
    params = {
        "date": date,
        "page": str(page),
    }

    r = await client.get(url, params=params)
    data = r.json()

    response = data.get("response")
    bet_count = len(response)
    logging.info(
        f"Got bets for date {date}, page {page}. Bet count: {bet_count}. Status: {r.status_code}. Data: {r.text[:45]}"
    )
    return response


async def get_bets_pagination(client: AsyncClient, date):
    url = get_api_url("/odds")
    params = {
        "date": date,
    }

    r = await client.get(url, params=params)
    data = r.json()

    total_pages = data["paging"]["total"]

    logging.info(
        f"Got pagination for bets on {date}. Status: {r.status_code}. Total pages: {total_pages}"
    )
    return total_pages
