import asyncio
import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_expression

from oddsapi.database.repository.season import upsert_season
from oddsapi.database.models import League, Season, Fixture, Bet


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


async def get_league_count(session: AsyncSession) -> int:
    stmt = select(func.count(League.id))
    return (await session.scalars(stmt)).first()


async def get_leagues_with_fixtures(
    session: AsyncSession, bookmaker: str
) -> list[League]:
    """
    find all leagues that have at least one Fixture
    """
    cutoff_period = 14  # days

    # two weeks forward date
    date = datetime.datetime.now() + datetime.timedelta(days=cutoff_period)

    fixture_cte = (
        select(Fixture.league_id, func.count().label("league_count"))
        .group_by(Fixture.league_id)
        .where((Fixture.date < date) & (Fixture.bets.any(Bet.bookmaker == bookmaker)))
        .cte("fixture_cte")
    )

    stmt = (
        select(League, fixture_cte.c.league_count)
        .join(fixture_cte, League.id == fixture_cte.c.league_id)
        .order_by(fixture_cte.c.league_count.desc())
        .options(with_expression(League.fixture_count, fixture_cte.c.league_count))
    )

    print(stmt.compile(compile_kwargs={"literal_binds": True}))

    return (await session.scalars(stmt)).all()  # noqa
