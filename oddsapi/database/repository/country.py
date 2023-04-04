from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.models import Country


async def upsert_country(country_data: dict, session: AsyncSession):
    update = True

    # sqlalchemy statement to find first country by name
    stmt = select(Country).where(Country.name == country_data["name"])
    country = (await session.scalars(stmt)).first()

    if not country:
        update = False
        country = Country()
        country.name = country_data["name"]

    country.code = country_data["code"]
    country.flag = country_data["flag"]

    session.add(country)

    return update


async def find_all_countries(session: AsyncSession):
    stmt = select(Country)

    countries = (await session.scalars(stmt)).all()
    return countries


async def delete_all_countries(session: AsyncSession):
    stmt = delete(Country)
    await session.execute(stmt)