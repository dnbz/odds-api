from oddsapi.database.init import SessionLocal
from oddsapi.database.repository.bet import delete_all_bets
from oddsapi.database.repository.bookmaker import delete_all_bookmakers
from oddsapi.database.repository.country import delete_all_countries
from oddsapi.database.repository.fixture import delete_all_fixtures
from oddsapi.database.repository.league import delete_all_leagues
from oddsapi.database.repository.notification import delete_notifications
from oddsapi.database.repository.team import delete_all_teams


async def clean_static():
    async with SessionLocal() as session:
        await delete_all_leagues(session)
        await delete_all_countries(session)
        await delete_all_bookmakers(session)
        await delete_all_teams(session)


async def clean_matches():
    async with SessionLocal() as session:
        await delete_all_bets(session)
        await delete_all_fixtures(session)


async def clean_notify():
    async with SessionLocal() as session:
        await delete_notifications(session)
        await session.commit()


async def clean_all():
    await clean_notify()
    await clean_matches()
    await clean_static()
