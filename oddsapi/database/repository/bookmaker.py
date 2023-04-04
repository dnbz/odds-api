from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.models import Bookmaker


async def upsert_bookmaker(bookmaker_data: dict, session: AsyncSession):
    stmt = select(Bookmaker).where(Bookmaker.source_id == bookmaker_data["id"])
    bookmaker = (await session.scalars(stmt)).first()

    update = True
    if not bookmaker:
        update = False
        bookmaker = Bookmaker()
        bookmaker.source_id = bookmaker_data["id"]

    bookmaker.name = bookmaker_data["name"]

    session.add(bookmaker)

    return update


async def delete_all_bookmakers(session: AsyncSession):
    stmt = delete(Bookmaker)
    await session.execute(stmt)