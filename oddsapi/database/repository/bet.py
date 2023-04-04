import logging
from datetime import datetime, timedelta

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.data_models import (
    BetcityEvent,
    FonbetEvent,
    MarathonEvent,
    PinnacleEvent,
)
from oddsapi.database.models import Bet, Fixture


async def upsert_apifootball_bet(
    bet_data: dict, bookmaker_data: dict, session: AsyncSession
):
    fixture_id = bet_data["fixture"]["id"]

    stmt = select(Fixture).where(Fixture.source_id == fixture_id)
    fixture = (await session.scalars(stmt)).first()

    if not fixture:
        logging.warning(f"Fixture with id {fixture_id} not found for bet.")

    update = True

    bet_stmt = select(Bet).where(
        Bet.fixture_id == fixture.id, Bet.bookmaker == bookmaker_data["name"]
    )

    bet = (await session.scalars(bet_stmt)).first()

    if not bet:
        update = False
        bet = Bet()
        bet.fixture = fixture
        bet.bookmaker = bookmaker_data["name"]

    bet.source = "apifootball"
    bet.source_update = datetime.fromisoformat(bet_data["update"])

    # https://www.api-football.com/documentation-v3#tag/Odds-(Pre-Match)/operation/get-odds
    for bookmaker_bet in bookmaker_data["bets"]:
        if bookmaker_bet.get("name") == "Match Winner":
            bet.home_win = float(bookmaker_bet["values"][0]["odd"])
            bet.draw = float(bookmaker_bet["values"][1]["odd"])
            bet.away_win = float(bookmaker_bet["values"][2]["odd"])

        elif bookmaker_bet.get("name") == "Goals Over/Under":
            for total in bookmaker_bet["values"]:
                if total.get("value") == "Over 2.5":
                    bet.total_over25 = float(total["odd"])
                elif total.get("value") == "Under 2.5":
                    bet.total_under25 = float(total["odd"])

    session.add(bet)

    return update


async def upsert_betcity_bet(
    event: BetcityEvent, date: datetime, fixture: Fixture, session: AsyncSession
) -> bool:
    bet = None
    update = False
    for fixture_bet in fixture.bets:
        if fixture_bet.bookmaker == "betcity":
            logging.info(
                f"This betcity bet is already in db for fixture with id {fixture.id}. Updating..."
            )
            update = True
            bet = fixture_bet

    five_min_ago = datetime.now() - timedelta(minutes=5)
    if (
        bet is not None
        and (bet.home_win != event.home_team)
        and (bet.updated_at.replace(tzinfo=None) > five_min_ago)
    ):
        logging.warning(
            "This betcity bet was modified less than five minutes ago"
            " and now we are trying to update it with values different from previous one."
            "This could be a bug."
        )

    if not bet:
        update = False
        bet = Bet()
        bet.fixture = fixture
        bet.bookmaker = "betcity"
        bet.source = "parser"
        bet.source_update = date

        logging.info(f"Adding bet from betcity for fixture with id {fixture.id}...")

    bet.home_win = event.home_team
    bet.draw = event.draw
    bet.away_win = event.away_team

    # b.total_over25 = float(total["odd"])
    # b.total_under25 = float(total["odd"])

    session.add(bet)
    logging.log(
        5, f"imported bet for betcity with fixture id {fixture.id} successfully"
    )

    return update


async def upsert_marathon_bet(
    event: MarathonEvent, date: datetime, fixture: Fixture, session: AsyncSession
) -> bool:
    bet = None
    update = False
    for fixture_bet in fixture.bets:
        if fixture_bet.bookmaker == "marathon":
            logging.info(
                f"This betcity bet is already in db for fixture with id {fixture.id}. Updating..."
            )
            update = True
            bet = fixture_bet

    five_min_ago = datetime.now() - timedelta(minutes=5)
    if (
        bet is not None
        and (bet.home_win != event.home_team)
        and (bet.updated_at.replace(tzinfo=None) > five_min_ago)
    ):
        logging.warning(
            "This marathon bet was modified less than five minutes ago"
            " and now we are trying to update it with values different from previous one."
            "This could be a bug."
        )

    if not bet:
        update = False
        bet = Bet()
        bet.fixture = fixture
        bet.bookmaker = "marathon"
        bet.source = "parser"
        bet.source_update = date

        logging.info(f"Adding bet from marathon for fixture with id {fixture.id}...")

    bet.home_win = event.home_team
    bet.draw = event.draw
    bet.away_win = event.away_team

    # b.total_over25 = float(total["odd"])
    # b.total_under25 = float(total["odd"])

    session.add(bet)
    logging.log(
        5, f"imported bet for marathon with fixture id {fixture.id} successfully"
    )

    return update


async def get_bet_bookmakers(session: AsyncSession) -> bool:
    # find all bookmakers using group by from Bet table. Order by count
    stmt = (
        select(Bet.bookmaker, func.count())
        .group_by(Bet.bookmaker)
        .order_by(func.count().desc())
    )
    bookmakers = (await session.execute(stmt)).all()
    return bookmakers


async def upsert_pinnacle_bet(
    event: PinnacleEvent, date: datetime, fixture: Fixture, session: AsyncSession
) -> bool:
    bet = None
    update = False
    for fixture_bet in fixture.bets:
        if fixture_bet.bookmaker == "pinnacle":
            logging.info(
                f"This pinnacle bet is already in db for fixture with id {fixture.id}. Updating..."
            )
            update = True
            bet = fixture_bet

    five_min_ago = datetime.now() - timedelta(minutes=5)
    if (
        bet is not None
        and (bet.home_win != event.home_team)
        and (bet.updated_at.replace(tzinfo=None) > five_min_ago)
    ):
        logging.warning(
            "This pinnacle bet was modified less than five minutes ago"
            " and now we are trying to update it with values different from previous one."
            "This could be a bug."
        )

    if not bet:
        update = False
        bet = Bet()
        bet.fixture = fixture
        bet.bookmaker = "pinnacle"
        bet.source = "parser"
        bet.source_update = date

        logging.info(f"Adding bet from pinnacle for fixture with id {fixture.id}...")

    bet.home_win = event.home_team
    bet.draw = event.draw
    bet.away_win = event.away_team

    # b.total_over25 = float(total["odd"])
    # b.total_under25 = float(total["odd"])

    session.add(bet)
    logging.log(
        5, f"imported bet for pinnacle with fixture id {fixture.id} successfully"
    )

    return update


async def upsert_fonbet_bet(
    event: FonbetEvent, date: datetime, fixture: Fixture, session: AsyncSession
) -> bool:
    bet = None
    update = False
    for fixture_bet in fixture.bets:
        if fixture_bet.bookmaker == "fonbet":
            logging.info(
                f"This betcity bet is already in db for fixture with id {fixture.id}. Updating..."
            )
            update = True
            bet = fixture_bet

    five_min_ago = datetime.now() - timedelta(minutes=5)
    if (
        bet is not None
        and (bet.home_win != event.home_team)
        and (bet.updated_at.replace(tzinfo=None) > five_min_ago)
    ):
        logging.warning(
            "This fonbet bet was modified less than five minutes ago"
            " and now we are trying to update it with values different from previous one."
            "This could be a bug."
        )

    if not bet:
        update = False
        bet = Bet()
        bet.fixture = fixture
        bet.bookmaker = "fonbet"
        bet.source = "parser"
        bet.source_update = date

        logging.info(f"Adding bet from fonbet for fixture with id {fixture.id}...")

    bet.home_win = event.home_team
    bet.draw = event.draw
    bet.away_win = event.away_team

    # b.total_over25 = float(total["odd"])
    # b.total_under25 = float(total["odd"])

    session.add(bet)
    logging.log(5, f"imported bet for fonbet with fixture id {fixture.id} successfully")

    return update


async def delete_all_bets(session: AsyncSession):
    stmt = delete(Bet)
    await session.execute(stmt)
