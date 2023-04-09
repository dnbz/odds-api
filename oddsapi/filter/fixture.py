from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import percentile_disc, func, now

from oddsapi.database.models import Bet, Fixture
from oddsapi.settings import DEVIATION_THRESHOLD, MAX_ODDS, REFERENCE_BOOKMAKER


def _get_select_filtered_fixtures(
    deviation_threshold: int = DEVIATION_THRESHOLD,
    max_odds: int = MAX_ODDS,
    reference_bookmaker: str | None = REFERENCE_BOOKMAKER,
):
    """Finds all fixtures that match the deviation criteria. Returns a SQLAlchemy Select object"""
    filtering_columns = [Bet.away_win, Bet.home_win, Bet.draw]
    col_names = [col.name for col in filtering_columns]

    median_cols = []
    for column in col_names:
        clause = (
            percentile_disc(0.5)
            .within_group(getattr(Bet, column))
            .label(f"median_{column}")
        )

        median_cols.append(clause)

    avg_stmt = (
        select(
            *median_cols,
            Bet.fixture_id,
        )
        .group_by(Bet.fixture_id)
        .cte("cte_avg")
    )

    bet_filters = []
    for column in col_names:
        deviation_clause = (
            func.abs(getattr(Bet, column) - getattr(avg_stmt.c, f"median_{column}"))
            > (getattr(avg_stmt.c, f"median_{column}") / 100) * deviation_threshold
        )

        odds_clause = getattr(Bet, column) < max_odds

        # Bet should be both within the odds limit and above the deviation threshold
        clause = odds_clause & deviation_clause

        bet_filters.append(clause)

    # filter by bookmaker
    if reference_bookmaker:
        where_clause = (
            (Fixture.date > now())
            & or_(*bet_filters)
            & Fixture.bets.any(Bet.bookmaker == reference_bookmaker)
        )
    else:
        where_clause = (Fixture.date > now()) & or_(*bet_filters)

    stmt = (
        select(Fixture)
        .join(Bet)
        .join(avg_stmt, avg_stmt.c.fixture_id == Bet.fixture_id)
        .where(where_clause)
    )

    stmt = stmt.options(joinedload(Fixture.bets), joinedload(Fixture.notifications))
    # print(stmt.compile(compile_kwargs={"literal_binds": True}))

    return stmt


async def find_filtered_fixtures(
    session: AsyncSession,
    deviation_threshold: float = DEVIATION_THRESHOLD,
    max_odds: float = MAX_ODDS,
    reference_bookmaker: str | None = REFERENCE_BOOKMAKER,
) -> list[Fixture] | None:
    stmt = _get_select_filtered_fixtures(
        deviation_threshold, max_odds, reference_bookmaker
    )

    fixtures = (await session.scalars(stmt)).unique().all()

    return fixtures  # noqa


async def find_unnotified_fixtures(session: AsyncSession) -> list[Fixture] | None:
    stmt = (
        _get_select_filtered_fixtures()
        .where(~Fixture.notifications.any())
        .options(joinedload(Fixture.bets), joinedload(Fixture.notifications))
    )

    # print raw sql with parameters
    # print(stmt.compile(compile_kwargs={"literal_binds": True}))

    fixtures = (await session.scalars(stmt)).unique().all()

    return fixtures  # noqa


class FixtureFinder:
    """Contains business logic that determines what fixtures should be displayed to the end user"""

    def __init__(self, session: AsyncSession):
        self.session = session
