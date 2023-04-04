import asyncio
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.repository.season import upsert_season
from oddsapi.database.models import League, Season


async def upsert_league(data: dict, session: AsyncSession):
    league_data = data["league"]
    country_data = data["country"]
    seasons_data = data["seasons"]

    stmt = select(League).where(League.source_id == league_data["id"])
    league = (await session.scalars(stmt)).first()

    update = True
    if not league:
        update = False
        league = League()
        league.source_id = league_data["id"]

    league.country = country_data["name"]
    league.country_code = country_data["code"]
    league.country_flag = country_data["flag"]
    league.name = league_data["name"]
    league.type = league_data["type"]
    league.logo = league_data["logo"]

    # return league
    session.add(league)

    # delete all seasons for this league
    delete_seasons_stmt = (
        delete(Season)
        .where(Season.league_id == league.id)
        .execution_options(synchronize_session="fetch")
    )
    await session.execute(delete_seasons_stmt)

    update_season_coros = [
        upsert_season(season, league, session) for season in seasons_data
    ]

    await asyncio.gather(*update_season_coros)

    return update


async def delete_all_leagues(session: AsyncSession):
    stmt = delete(League)
    await session.execute(stmt)
