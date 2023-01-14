import asyncio
import io
from datetime import timedelta
from string import Template

from PIL import Image
from plotly import figure_factory as ff
from plotly import graph_objects as go
from redis.asyncio import Redis

from oddsapi.db import init_db, redis_connect
from oddsapi.models import Fixture
from oddsapi.settings import DEVIATION_THRESHOLD


def format_fixture(f: Fixture) -> list:
    rows = []
    for bet in f.bets:
        date_format = "%d %b. %H:%M:%S"
        date = bet.source_update.strftime(date_format)

        match_date = f.date.strftime(date_format)

        rows.append(
            [
                f.home_team_name,
                f.away_team_name,
                bet.home_win,
                bet.draw,
                bet.away_win,
                bet.bookmaker,
                date,
                match_date,
            ]
        )

    rows.append(["", "", "", "", "", "", ""])
    return rows


async def filter_fixtures() -> list[Fixture] | None:
    """Finds all fixtures that match the requested criteria"""
    # round(avg(b.home_win), 5) as avg_home_win,
    # round(avg(b.draw), 5) as avg_draw,
    # round(avg(b.away_win), 5) as avg_away_win,
    sql = Template(
        """WITH cte_avg as (
    SELECT
            percentile_disc(0.5) WITHIN GROUP(ORDER BY home_win) as avg_home_win,
            percentile_disc(0.5) WITHIN GROUP(ORDER BY away_win) as avg_away_win,
            percentile_disc(0.5) WITHIN GROUP(ORDER BY draw) as avg_draw,
            b.fixture_id
        from bet b
        group by b.fixture_id
    )
    select f.*
    from fixture f
             inner join bet b on f.id = b.fixture_id
             join cte_avg on b.fixture_id = cte_avg.fixture_id
    where (f.date > NOW()) AND 
    (abs(home_win - avg_home_win) > ((avg_home_win/100)* $threshold)
    or abs(away_win - avg_away_win) > ((avg_away_win/100) * $threshold)
    or abs(draw - avg_draw) > ((avg_draw/100) * $threshold)
    )
    group by f.id;"""
    ).substitute(threshold=DEVIATION_THRESHOLD)

    fixtures = await Fixture.all().prefetch_related("bets").raw(sql)

    return fixtures


async def get_unnotified_fixtures() -> list[Fixture] | None:
    fixtures = await filter_fixtures()
    for fixture in fixtures:
        await fixture.fetch_related("bets")
        await fixture.fetch_related("notifications")

    fixtures = [fixture for fixture in fixtures if not fixture.notifications]

    return fixtures


def get_table_fig(fixtures: list[Fixture]) -> go.Figure:
    header = [
        "Хозяева",
        "Гости",
        "Победа хозяев",
        "Ничья",
        "Победа Гостей",
        "БК",
        "Обновлено",
        "Дата проведения",
    ]
    layout = go.Layout(
        autosize=False, margin={"l": 0, "r": 0, "t": 20, "b": 0}, width=1200
    )

    data = []
    for fixture in fixtures:
        data.extend(format_fixture(fixture))

    cells = [header, *data]
    fig = ff.create_table(cells)
    fig = fig.update_layout(layout)

    return fig


def gen_img(fig: go.Figure) -> io.BytesIO:
    photo_bytes = fig.to_image(format="png")
    photo = io.BytesIO(photo_bytes)
    photo.name = "plot.png"

    return photo


async def get_cache_img(r: Redis) -> io.BytesIO:
    """Gets cached image for filtered fixtures if it exists. Caches image and returns it if it doesn't"""
    redis_key = "tg_fixture_report_img"
    cache_minutes = 10

    if await r.exists(redis_key):
        photo_bytes = await r.get(redis_key)
        await r.close()

        return io.BytesIO(photo_bytes)

    fixtures = await filter_fixtures()
    for fixture in fixtures:
        await fixture.fetch_related("bets")

    fig = get_table_fig(fixtures)
    io_data = fig_to_bytesio(fig)

    await r.setex(redis_key, timedelta(minutes=cache_minutes), value=io_data.getvalue())

    await r.close()
    return io_data


def fig_to_bytesio(fig: go.Figure) -> io.BytesIO:
    io_data = io.BytesIO()
    fig.write_image(file=io_data, format="png")

    return io_data
