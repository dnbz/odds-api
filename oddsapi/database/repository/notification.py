from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.models import Notification


async def delete_notifications(session: AsyncSession):
    stmt = delete(Notification)
    await session.execute(stmt)
