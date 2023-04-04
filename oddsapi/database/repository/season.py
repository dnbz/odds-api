from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.models import League, Season


async def upsert_season(season_data: dict, league: League, session: AsyncSession):
    stmt = select(Season).where(
        and_(Season.league_id == league.id, Season.year == season_data["year"])
    )

    season = (await session.scalars(stmt)).first()

    update = True
    if not season:
        update = False
        season = Season()
        season.year = season_data["year"]
        season.league = league

    season.start = datetime.strptime(season_data["start"], "%Y-%m-%d")
    season.end = datetime.strptime(season_data["end"], "%Y-%m-%d")
    season.current = season_data["current"]

    if season_data.get("coverage"):
        season.odds_coverage = season_data["coverage"]["odds"]

    session.add(season)

    return update
