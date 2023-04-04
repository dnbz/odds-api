import io
from datetime import timedelta

from plotly import graph_objects as go, figure_factory as ff
from redis.asyncio import Redis  # noqa

from oddsapi.database.models import Fixture


def fig_to_bytesio(fig: go.Figure) -> io.BytesIO:
    io_data = io.BytesIO()
    fig.write_image(file=io_data, format="png")

    return io_data


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


async def get_cache_img(r: Redis, fixtures: list[Fixture]) -> io.BytesIO:
    """Gets cached image for filtered fixtures if it exists. Caches image and returns it if it doesn't"""
    redis_key = "tg_fixture_report_img"
    cache_minutes = 10

    if await r.exists(redis_key):
        photo_bytes = await r.get(redis_key)
        await r.close()

        return io.BytesIO(photo_bytes)

    io_data = gen_img_from_fixtures(fixtures)

    await r.setex(redis_key, timedelta(minutes=cache_minutes), value=io_data.getvalue())

    await r.close()
    return io_data


def gen_img_from_fixtures(fixtures: list[Fixture]) -> io.BytesIO:
    fig = get_table_fig(fixtures)
    photo = gen_img(fig)

    return photo
