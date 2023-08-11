from dataclasses import dataclass
from enum import Enum

import sqlalchemy
from sqlalchemy import (
    select,
    or_,
    and_,
    true,
    case,
    literal_column,
    union_all,
    literal,
    not_,
    lateral,
    cast,
    type_coerce,
    join,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, with_expression, aliased
from sqlalchemy.sql.functions import func, now

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
    all_bets_must_match: bool = True
    league_ids: list[int] | None = None


# def _get_select_filtered_fixtures(
#     params: FixtureQueryParams,
# ):
#     """Finds all fixtures that match the deviation criteria. Returns a SQLAlchemy Select object"""
#     filtering_columns = [Bet.away_win, Bet.home_win, Bet.draw]
#     col_names = [col.name for col in filtering_columns]
#
#     avg_columns = []
#     for column in col_names:
#         clause = getattr(Bet, column).label(f"median_{column}")
#
#         avg_columns.append(clause)
#
#     cte_avg = (
#         select(
#             *avg_columns,
#             Bet.fixture_id,
#         )
#         .join(Bet.fixture)
#         .where((Fixture.date > now()) & (Bet.bookmaker == params.reference_bookmaker))
#         # .group_by(Bet.fixture_id)
#         .cte("cte_avg")
#     )
#
#     bet_filters = []
#     for column in col_names:
#         avg_col = getattr(cte_avg.c, f"median_{column}")
#         fixture_col = getattr(Bet, column)
#
#         if params.deviation_strategy == DeviationStrategy.PERCENT.value:
#             deviation = (avg_col / 100) * params.percent_deviation_threshold
#             if params.deviation_direction == DeviationDirection.BOTH.value:
#                 deviation_clause = (
#                     func.abs(fixture_col - avg_col)
#                     > (avg_col / 100) * params.percent_deviation_threshold
#                 )
#             elif params.deviation_direction == DeviationDirection.HIGHER.value:
#                 deviation_clause = (fixture_col - avg_col) > deviation
#             elif params.deviation_direction == DeviationDirection.LOWER.value:
#                 deviation_clause = (avg_col - fixture_col) > deviation
#         else:
#             # absolute deviation
#             deviation = params.absolute_deviation_threshold
#             if params.deviation_direction == DeviationDirection.BOTH.value:
#                 deviation_clause = func.abs(fixture_col - avg_col) > deviation
#             elif params.deviation_direction == DeviationDirection.HIGHER.value:
#                 deviation_clause = (fixture_col - avg_col) > deviation
#             elif params.deviation_direction == DeviationDirection.LOWER.value:
#                 deviation_clause = (avg_col - fixture_col) > deviation
#
#         # odds_clause = getattr(Bet, column) < params.max_odds
#         odds_clause = getattr(cte_avg.c, f"median_{column}") < params.max_odds
#
#         # Bet should be both within the odds limit and above the deviation threshold
#         clause = odds_clause & deviation_clause  # noqa
#
#         if params.all_bets_must_match:
#             clause = func.bool_and(clause)
#
#         clause = clause.label(f"condition_{column}")
#
#         bet_filters.append(clause)
#
#     condition_stmt = select(Bet.fixture_id).join(
#         cte_avg, cte_avg.c.fixture_id == Bet.fixture_id
#     )
#
#     if params.all_bets_must_match:
#         condition_stmt = condition_stmt.where(
#             Bet.bookmaker != params.reference_bookmaker
#         )
#         condition_stmt = condition_stmt.group_by(Bet.fixture_id)
#
#     for bet_filter in bet_filters:
#         condition_stmt = condition_stmt.add_columns(bet_filter)
#
#     cte_condition = condition_stmt.cte("cte_condition")
#
#     condition_columns = [
#         # label is used to prevent usage of joined cte prefix
#         getattr(cte_condition.c, f"condition_{col}").label(f"condition_{col}")
#         for col in col_names
#     ]
#
#     stmt = (
#         select(Fixture)
#         .join(cte_condition, cte_condition.c.fixture_id == Fixture.id)
#         .where(or_(*condition_columns))
#     )
#
#     # dynamically load the columns that represent which condition has been met
#     expression = [
#         with_expression(
#             getattr(Fixture, f"condition_{col}"),
#             getattr(cte_condition.c, f"condition_{col}"),
#         )
#         for col in col_names
#     ]
#     stmt = stmt.options(*expression)
#
#     stmt = stmt.where(Fixture.bets.any(Bet.bookmaker == params.reference_bookmaker))
#
#     if params.league_ids:
#         stmt = stmt.where(Fixture.league_id.in_(params.league_ids))
#
#     # print(stmt.compile(compile_kwargs={"literal_binds": True}))
#
#     return stmt


def get_comparison_clause(
    params: FixtureQueryParams,
    reference_col: sqlalchemy.Column,
    compared_col: sqlalchemy.Column,
):
    if params.deviation_strategy == DeviationStrategy.PERCENT.value:
        deviation = reference_col * params.percent_deviation_threshold
        if params.deviation_direction == DeviationDirection.BOTH.value:
            deviation_clause = (
                func.abs(compared_col - reference_col)
                > reference_col * params.percent_deviation_threshold
            )
        elif params.deviation_direction == DeviationDirection.HIGHER.value:
            deviation_clause = (compared_col - reference_col) > deviation
        elif params.deviation_direction == DeviationDirection.LOWER.value:
            deviation_clause = (reference_col - compared_col) > deviation
    else:
        # absolute deviation
        deviation = params.absolute_deviation_threshold
        if params.deviation_direction == DeviationDirection.BOTH.value:
            deviation_clause = func.abs(compared_col - reference_col) > deviation
        elif params.deviation_direction == DeviationDirection.HIGHER.value:
            deviation_clause = (compared_col - reference_col) > deviation
        elif params.deviation_direction == DeviationDirection.LOWER.value:
            deviation_clause = (reference_col - compared_col) > deviation

    if params.max_odds:
        odds_clause = compared_col < params.max_odds
        deviation_clause = deviation_clause & odds_clause

    return deviation_clause


def _get_select_filtered_fixtures_jsonb(
    params: FixtureQueryParams,
):
    # also meh, type coercion is needed to get the jsonb_array_elements to work
    totals_elem = type_coerce(
        func.jsonb_array_elements(Bet.totals).column_valued("totals_elem"), JSONB
    )

    totals_table = lateral(
        func.jsonb_array_elements(Bet.totals).table_valued("totals_elem")
    ).alias("totals_elem")

    totals_reference = (
        select(
            Bet.fixture_id,
            totals_elem["total"].astext.cast(sqlalchemy.Numeric).label("total"),
            totals_elem["total_over"]
            .astext.cast(sqlalchemy.Numeric)
            .label("total_over"),
            totals_elem["total_under"]
            .astext.cast(sqlalchemy.Numeric)
            .label("total_under"),
        ).where(Bet.bookmaker == params.reference_bookmaker)
    ).cte("totals_reference")

    outcomes_reference = (
        select(
            Bet.fixture_id,
            Bet.outcomes["home_team"]
            .astext.cast(sqlalchemy.Numeric)
            .label("home_team"),
            Bet.outcomes["draw"].astext.cast(sqlalchemy.Numeric).label("draw"),
            Bet.outcomes["away_team"]
            .astext.cast(sqlalchemy.Numeric)
            .label("away_team"),
        ).where(Bet.bookmaker == params.reference_bookmaker)
    ).cte("outcomes_reference")

    # sqlalchemy is bad
    totals_elem_literal = literal_column("totals_elem", type_=JSONB)
    totals_comparison = (
        select(
            Bet.fixture_id,
            sqlalchemy.case(
                (
                    get_comparison_clause(
                        params,
                        totals_reference.c.total_over,
                        totals_elem_literal["total_over"].astext.cast(
                            sqlalchemy.Numeric
                        ),
                    ),
                    sqlalchemy.literal("totals over ")
                    + totals_elem_literal["total"].astext,
                ),
                (
                    get_comparison_clause(
                        params,
                        totals_reference.c.total_under,
                        totals_elem_literal["total_under"].astext.cast(
                            sqlalchemy.Numeric
                        ),
                    ),
                    sqlalchemy.literal("totals under ")
                    + totals_elem_literal["total"].astext,
                ),
            ).label("trigger"),
        )
        .join_from(Bet, totals_table, text("true"))
        .join(
            totals_reference,
            (Bet.fixture_id == totals_reference.c.fixture_id)
            & (
                totals_elem_literal["total"].astext.cast(sqlalchemy.Numeric)
                == totals_reference.c.total
            ),
        )
        .where(
            get_comparison_clause(
                params,
                totals_reference.c.total_over,
                totals_elem_literal["total_over"].astext.cast(sqlalchemy.Numeric),
            )
            | get_comparison_clause(
                params,
                totals_reference.c.total_under,
                totals_elem_literal["total_under"].astext.cast(sqlalchemy.Numeric),
            )
        )
    ).cte("totals_comparison")

    outcomes_comparison_condition_clauses = [
        get_comparison_clause(
            params,
            outcomes_reference.c.home_team,
            Bet.outcomes["home_team"].astext.cast(sqlalchemy.Numeric),
        ),
        get_comparison_clause(
            params,
            outcomes_reference.c.draw,
            Bet.outcomes["draw"].astext.cast(sqlalchemy.Numeric),
        ),
        get_comparison_clause(
            params,
            outcomes_reference.c.away_team,
            Bet.outcomes["away_team"].astext.cast(sqlalchemy.Numeric),
        ),
    ]

    if params.all_bets_must_match:
        outcomes_comparison_condition = and_(*outcomes_comparison_condition_clauses)
    else:
        outcomes_comparison_condition = or_(*outcomes_comparison_condition_clauses)

    outcomes_comparison = (
        select(
            Bet.fixture_id,
            sqlalchemy.case(
                (
                    get_comparison_clause(
                        params,
                        outcomes_reference.c.home_team,
                        Bet.outcomes["home_team"].astext.cast(sqlalchemy.Numeric),
                    ),
                    sqlalchemy.literal("outcomes home_team"),
                ),
                (
                    get_comparison_clause(
                        params,
                        outcomes_reference.c.draw,
                        Bet.outcomes["draw"].astext.cast(sqlalchemy.Numeric),
                    ),
                    sqlalchemy.literal("outcomes draw"),
                ),
                (
                    get_comparison_clause(
                        params,
                        outcomes_reference.c.away_team,
                        Bet.outcomes["away_team"].astext.cast(sqlalchemy.Numeric),
                    ),
                    sqlalchemy.literal("outcomes away_team"),
                ),
            ).label("trigger"),
        )
        .join(
            outcomes_reference,
            Bet.fixture_id == outcomes_reference.c.fixture_id,
        )
        .where(
            outcomes_comparison_condition
            # get_comparison_clause(
            #     params,
            #     outcomes_reference.c.home_team,
            #     Bet.outcomes["home_team"].astext.cast(sqlalchemy.Numeric),
            # )
            # | get_comparison_clause(
            #     params,
            #     outcomes_reference.c.draw,
            #     Bet.outcomes["draw"].astext.cast(sqlalchemy.Numeric),
            # )
            # | get_comparison_clause(
            #     params,
            #     outcomes_reference.c.away_team,
            #     Bet.outcomes["away_team"].astext.cast(sqlalchemy.Numeric),
            # )
        )
    ).cte("outcomes_comparison")

    combined_triggers = (
        select(totals_comparison.c.fixture_id, totals_comparison.c.trigger)
        .where(totals_comparison.c.trigger != None)
        .union_all(
            select(
                outcomes_comparison.c.fixture_id, outcomes_comparison.c.trigger
            ).where(outcomes_comparison.c.trigger != None)
        )
    ).cte("combined_triggers")

    final_cte = (
        select(
            Fixture,
            sqlalchemy.func.string_agg(combined_triggers.c.trigger, ", ").label(
                "trigger"
            ),
        )
        .group_by(Fixture.id)
        .join(
            combined_triggers,
            Fixture.id == combined_triggers.c.fixture_id,
        )
    )

    if params.league_ids:
        final_cte = final_cte.where(Fixture.league_id.in_(params.league_ids))

    final_cte = final_cte.cte("final_cte")

    stmt = select(Fixture).join(final_cte, Fixture.id == final_cte.c.id)

    # dynamically load the columns that represent which condition has been met
    expression = with_expression(
        getattr(Fixture, f"trigger"),
        getattr(final_cte.c, f"trigger"),
    )

    stmt = stmt.options(expression)

    # stmt = stmt.options(expression)
    print(stmt.compile(compile_kwargs={"literal_binds": True}))

    return stmt


async def find_filtered_fixtures(
    session: AsyncSession,
    params: FixtureQueryParams,
) -> list[Fixture] | None:
    stmt = _get_select_filtered_fixtures_jsonb(params)
    print(stmt.compile(compile_kwargs={"literal_binds": True}))
    print("\n\n\n")

    stmt = stmt.options(
        joinedload(Fixture.bets),
        joinedload(Fixture.notifications),
        joinedload(Fixture.league),
    )

    fixtures = (await session.scalars(stmt)).unique().all()

    return fixtures  # noqa


async def find_unnotified_fixtures(session: AsyncSession) -> list[Fixture] | None:
    stmt = (
        _get_select_filtered_fixtures_jsonb(FixtureQueryParams())
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
