import logging
import re
from datetime import datetime

from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import now
from sqlalchemy import func

from oddsapi.database.models import Fixture, League


async def upsert_fixture(data: dict, session: AsyncSession):
    fixture_data = data["fixture"]
    league_data = data["league"]
    home_team = data["teams"]["home"]
    away_team = data["teams"]["away"]

    stmt = select(Fixture).where(Fixture.source_id == fixture_data["id"])
    fixture = (await session.scalars(stmt)).first()

    update = True
    if not fixture:
        update = False
        fixture = Fixture()
        fixture.source_id = fixture_data["id"]

    fixture.timezone = fixture_data["timezone"]
    fixture.date = datetime.fromisoformat(fixture_data["date"])

    fixture.league_season = league_data["season"]

    fixture.home_team_name = home_team["name"]
    fixture.home_team_logo = home_team["logo"]
    fixture.home_team_source_id = home_team["id"]

    fixture.away_team_name = away_team["name"]
    fixture.away_team_logo = away_team["logo"]
    fixture.away_team_source_id = away_team["id"]

    # don't update existing relations
    if not update:
        league_stmt = select(League).where(League.source_id == league_data["id"])
        league = (await session.scalars(league_stmt)).first()

        if league:
            fixture.league = league
        else:
            logging.warning(
                f"No league with id {league_data['id']} found for fixture {dict(fixture)}"
            )

    session.add(fixture)

    return update


async def find_fixture_ilike(
    home_team: str, away_team: str, date: datetime, session: AsyncSession
) -> Fixture | None:
    # func.date is used to round datetime to date
    stmt = (
        select(Fixture)
        .where(
            func.unaccent(Fixture.home_team_name).ilike(f"%{home_team}%")
            & func.unaccent(Fixture.away_team_name).ilike(f"%{away_team}%")
            & (Fixture.date > now())
            & (Fixture.date >= func.date(date))
            & (Fixture.date < (func.date(date) + text(r"interval '1 day'")))
        )
        .options(joinedload(Fixture.bets), joinedload(Fixture.notifications))
    )

    fixture = (await session.scalars(stmt)).first()

    return fixture  # noqa


def _gen_soft_search_pattern(string: str) -> str:
    """Convert text to sql query for search.
    Adds | between words and discards words < 3 chars long"""

    # remove whitespace
    string = re.sub(r"\s+", " ", string.strip())
    # dashes are sometimes used in place of spaces
    string = string.replace("-", " ")

    words = string.split(" ")

    if len(words) < 2:
        result = f".*{words[0]}.*"
        return result

    words = [word for word in words if len(word) > 3]

    result = "|".join(words)

    return f".*({result}).*"


# .*one|two|three.*


async def find_fixture_partial(
    home_team: str, away_team: str, date: datetime, session: AsyncSession
):
    # func.date is used to round datetime to date
    home_team = _gen_soft_search_pattern(home_team)
    away_team = _gen_soft_search_pattern(away_team)
    stmt = (
        select(Fixture)
        .where(
            func.unaccent(Fixture.home_team_name).regexp_match(home_team, flags="i")
            & func.unaccent(Fixture.away_team_name).regexp_match(away_team, flags="i")
            & (Fixture.date > now())
            & (Fixture.date >= func.date(date))
            & (Fixture.date < (func.date(date) + text(r"interval '1 day'")))
        )
        .options(joinedload(Fixture.bets), joinedload(Fixture.notifications))
    )

    # print raw sql in postgres dialect using literal binds compile
    # print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

    fixture = (await session.scalars(stmt)).first()

    return fixture  # noqa


async def delete_all_fixtures(session: AsyncSession):
    stmt = delete(Fixture)
    await session.execute(stmt)
