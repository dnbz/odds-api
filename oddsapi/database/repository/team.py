from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.models import Team


async def upsert_team(team_data: dict, country_id: int, session: AsyncSession):
    team_data = team_data["team"]

    stmt = select(Team).where(Team.source_id == team_data["id"])
    team = (await session.scalars(stmt)).first()

    update = True
    if not team:
        update = False
        team = Team()
        team.source_id = team_data["id"]

    team.name = team_data["name"]
    team.code = team_data["code"]
    team.logo = team_data["logo"]
    team.founded_at = team_data["founded"]
    team.national = team_data["national"]

    team.country_id = country_id

    session.add(team)

    return update


async def delete_all_teams(session: AsyncSession):
    stmt = delete(Team)
    await session.execute(stmt)
