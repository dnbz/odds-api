from dataclasses import dataclass
from enum import Enum

from sqlalchemy import select, or_, Sequence, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, with_expression
from sqlalchemy.sql.functions import percentile_disc, func, now

from oddsapi.database.models import Bet, Fixture
from oddsapi.settings import DEVIATION_THRESHOLD, MAX_ODDS, REFERENCE_BOOKMAKER


# deviation strategy enum
class DeviationStrategy(Enum):
    PERCENT = "percent"
    ABSOLUTE = "absolute"


class DeviationDirection(Enum):
    LOWER = "lower"
    HIGHER = "higher"
    BOTH = "both"


# default values
DEFAULT_ODDS_THRESHOLD = MAX_ODDS
DEFAULT_DEVIATION_STRATEGY = DeviationStrategy.PERCENT.value
DEFAULT_DEVIATION_DIRECTION = DeviationDirection.BOTH.value
DEFAULT_PERCENT_DEVIATION = DEVIATION_THRESHOLD
DEFAULT_ABSOLUTE_DEVIATION = 1


@dataclass
class FixtureQueryParams:
    """Fixture query parameters"""

    percent_deviation_threshold: int = DEFAULT_PERCENT_DEVIATION
    absolute_deviation_threshold: int = DEFAULT_ABSOLUTE_DEVIATION
    max_odds: int = DEFAULT_ODDS_THRESHOLD
    reference_bookmaker: str | None = REFERENCE_BOOKMAKER
    deviation_strategy: DeviationStrategy = DEFAULT_DEVIATION_STRATEGY
    deviation_direction: DeviationDirection = DEFAULT_DEVIATION_DIRECTION


def _get_select_filtered_fixtures(
    params: FixtureQueryParams,
):
    """Finds all fixtures that match the deviation criteria. Returns a SQLAlchemy Select object"""
    filtering_columns = [Bet.away_win, Bet.home_win, Bet.draw]
    col_names = [col.name for col in filtering_columns]

    # avg_columns = []
    # for column in col_names:
    #     clause = (
    #         percentile_disc(0.5)
    #         .within_group(getattr(Bet, column))
    #         .label(f"median_{column}")
    #     )
    #
    #     avg_columns.append(clause)

    # cte_avg = (
    #     select(
    #         *avg_columns,
    #         Bet.fixture_id,
    #     )
    #     .join(Bet.fixture)
    #     .where(Fixture.date > now())
    #     .group_by(Bet.fixture_id)
    #     .cte("cte_avg")
    # )

    avg_columns = []
    for column in col_names:
        clause = getattr(Bet, column).label(f"median_{column}")

        avg_columns.append(clause)

    cte_avg = (
        select(
            *avg_columns,
            Bet.fixture_id,
        )
        .join(Bet.fixture)
        .where((Fixture.date > now()) & (Bet.bookmaker == params.reference_bookmaker))
        # .group_by(Bet.fixture_id)
        .cte("cte_avg")
    )

    bet_filters = []
    for column in col_names:
        avg_col = getattr(cte_avg.c, f"median_{column}")
        fixture_col = getattr(Bet, column)

        if params.deviation_strategy == DeviationStrategy.PERCENT.value:
            deviation = (avg_col / 100) * params.percent_deviation_threshold
            if params.deviation_direction == DeviationDirection.BOTH.value:
                deviation_clause = (
                    func.abs(fixture_col - avg_col)
                    > (avg_col / 100) * params.percent_deviation_threshold
                )
            elif params.deviation_direction == DeviationDirection.HIGHER.value:
                deviation_clause = (fixture_col - avg_col) > deviation
            elif params.deviation_direction == DeviationDirection.LOWER.value:
                deviation_clause = (avg_col - fixture_col) > deviation
        else:
            # absolute deviation
            deviation = params.absolute_deviation_threshold
            if params.deviation_direction == DeviationDirection.BOTH.value:
                deviation_clause = func.abs(fixture_col - avg_col) > deviation
            elif params.deviation_direction == DeviationDirection.HIGHER.value:
                deviation_clause = (fixture_col - avg_col) > deviation
            elif params.deviation_direction == DeviationDirection.LOWER.value:
                deviation_clause = (avg_col - fixture_col) > deviation

        # odds_clause = getattr(Bet, column) < params.max_odds
        odds_clause = getattr(cte_avg.c, f"median_{column}") < params.max_odds

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
            getattr(Fixture, f"condition_{col}"),
            getattr(cte_condition.c, f"condition_{col}"),
        )
        for col in col_names
    ]
    stmt = stmt.options(*expression)

    if params.reference_bookmaker:
        stmt = stmt.where(Fixture.bets.any(Bet.bookmaker == params.reference_bookmaker))

    # print(stmt.compile(compile_kwargs={"literal_binds": True}))

    return stmt


async def find_filtered_fixtures(
    session: AsyncSession,
    params: FixtureQueryParams,
) -> list[Fixture] | None:
    stmt = _get_select_filtered_fixtures(params)

    stmt = stmt.options(
        joinedload(Fixture.bets),
        joinedload(Fixture.notifications),
        joinedload(Fixture.league),
    )

    fixtures = (await session.scalars(stmt)).unique().all()

    return fixtures  # noqa


async def find_unnotified_fixtures(session: AsyncSession) -> list[Fixture] | None:
    stmt = (
        _get_select_filtered_fixtures(FixtureQueryParams())
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
