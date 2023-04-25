from sqlalchemy import select, or_, Sequence, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, with_expression
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

    avg_columns = []
    for column in col_names:
        clause = (
            percentile_disc(0.5)
            .within_group(getattr(Bet, column))
            .label(f"median_{column}")
        )

        avg_columns.append(clause)

    cte_avg = (
        select(
            *avg_columns,
            Bet.fixture_id,
        )
        .join(Bet.fixture)
        .where(Fixture.date > now())
        .group_by(Bet.fixture_id)
        .cte("cte_avg")
    )

    bet_filters = []
    for column in col_names:
        deviation_clause = (
            func.abs(getattr(Bet, column) - getattr(cte_avg.c, f"median_{column}"))
            > (getattr(cte_avg.c, f"median_{column}") / 100) * deviation_threshold
        )

        odds_clause = getattr(Bet, column) < max_odds

        # Bet should be both within the odds limit and above the deviation threshold
        clause = (odds_clause & deviation_clause).label(f"condition_{column}")

        bet_filters.append(clause)

    condition_stmt = select(Bet.fixture_id).join(
        cte_avg, cte_avg.c.fixture_id == Bet.fixture_id
    )

    for bet_filter in bet_filters:
        condition_stmt = condition_stmt.add_columns(bet_filter)

    cte_condition = condition_stmt.cte("cte_condition")

    condition_columns = [
        # label is used to prevent usage of joined cte prefix
        getattr(cte_condition.c, f"condition_{col}").label(f"condition_{col}")
        for col in col_names
    ]

    stmt = (
        select(Fixture)
        .join(cte_condition, cte_condition.c.fixture_id == Fixture.id)
        .where(or_(*condition_columns))
    )

    # dynamically load the columns that represent which condition has been met
    expression = [
        with_expression(
            getattr(Fixture, f"condition_{col}"), getattr(cte_condition.c, f"condition_{col}")
        )
        for col in col_names
    ]
    stmt = stmt.options(*expression)

    if reference_bookmaker:
        stmt = stmt.where(Fixture.bets.any(Bet.bookmaker == reference_bookmaker))

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

    stmt = stmt.options(
        joinedload(Fixture.bets),
        joinedload(Fixture.notifications),
        joinedload(Fixture.league),
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
