import asyncio
import logging

import gradio as gr
import matplotlib
from gradio import State
from pandas import DataFrame

from oddsapi.database.init import SessionLocal
from oddsapi.database.repository.bet import get_bet_bookmakers
from oddsapi.filter.fixture import find_filtered_fixtures
from oddsapi.settings import (
    MAX_ODDS,
    DEVIATION_THRESHOLD,
    REFERENCE_BOOKMAKER,
    UI_PASSWORD,
    APP_ENV,
)

matplotlib.use("Agg")

import pandas as pd

MINIMUM_ODDS_THRESHOLD = 1.01
MAXIMUM_ODDS_THRESHOLD = 7
DEFAULT_ODDS_THRESHOLD = MAX_ODDS

MINIMUM_DEVIATION = 15
MAXIMUM_DEVIATION = 60
DEFAULT_DEVIATION = DEVIATION_THRESHOLD


def get_bookmakers():
    # return []
    async def async_get_bookmakers():
        SessionLocal().run
        async with SessionLocal() as session:
            data = await get_bet_bookmakers(session)
            return data

    if asyncio.get_event_loop().is_running():
        logging.info(
            "Event loop is already running, skipping async call and using default values for bookmakers."
        )
        return ["fonbet - 0", "marathon - 0", "pinnacle - 0", "betcity - 0j"]
    else:
        bookmaker_data = asyncio.run(async_get_bookmakers())

    # concatenate bookmaker names and count
    result = []
    for bookmaker in bookmaker_data:
        result.append(f"{bookmaker[0]} - {bookmaker[1]}")

    return result


def get_fixtures(
    bookmaker: str,
    deviation: float,
    odds_threshold: float,
):
    async def async_get_data():
        async with SessionLocal() as session:
            f = await find_filtered_fixtures(
                session,
                reference_bookmaker=bookmaker,
                deviation_threshold=deviation,
                max_odds=odds_threshold,
            )
            return f

    fixtures = asyncio.run(async_get_data())
    return fixtures


def fetch_events(
    state: dict,
):
    fixtures = get_fixtures(
        state["bookmaker"], state["deviation"], state["odds_threshold"]
    )

    event_data = []

    for fixture in fixtures:
        # conditions that were met to match this fixture
        match_conditions = []
        # iterate over dict keys and values
        for key, value in fixture.get_conditions().items():
            if value is True:
                match_conditions.append(key)

        match_condition = ", ".join(match_conditions)

        event_data.append(
            {
                "Id": fixture.id,
                "Home team": fixture.home_team_name,
                "Away team": fixture.away_team_name,
                "Date": fixture.date,
                "League": fixture.league.name,
                "Condition": match_condition,
            }
        )

    df = pd.DataFrame(event_data)
    return fixtures, df


# display the odds for a given fixture on select
def event_on_select(evt: gr.SelectData, data: DataFrame, fixtures: list, state: dict):
    row_id = evt.index[0]
    fixture_id = data.iloc[row_id]["Id"]

    fixture = next((f for f in fixtures if f.id == fixture_id), None)

    if fixture is None:
        return None

    # create a dataframe with the odds for the selected fixture
    odds_data = [
        {
            "Bookmaker": bet.bookmaker,
            "Home odds": bet.home_win,
            "Draw odds": bet.draw,
            "Away odds": bet.away_win,
        }
        for bet in fixture.bets
    ]
    # filter the dictionaries where "Bookmaker" is equal to "mybk"
    reference_bk_odds = [d for d in odds_data if d["Bookmaker"] == state["bookmaker"]]

    # filter the dictionaries where "Bookmaker" is not equal to "mybk"
    other_bk_odds = [d for d in odds_data if d["Bookmaker"] != state["bookmaker"]]

    # create a dataframe from the filtered dictionaries
    df = pd.DataFrame(reference_bk_odds + other_bk_odds)

    return df


# display the odds for a given fixture on select
def info_on_select(evt: gr.SelectData, data: DataFrame, fixtures: list, state: dict):
    row_id = evt.index[0]
    fixture_id = data.iloc[row_id]["Id"]

    fixture = next((f for f in fixtures if f.id == fixture_id), None)

    if fixture is None:
        return None

    # create a dataframe with the odds for the selected fixture
    data = {
        "Source update": fixture.source_update,
        "Date": fixture.date,
        "Away_team_logo": fixture.away_team_logo,
    }

    df = pd.DataFrame([data])

    return df


def get_default_state() -> dict:
    default_state = {
        "bookmaker": REFERENCE_BOOKMAKER,
        "deviation": DEFAULT_DEVIATION,
        "odds_threshold": DEFAULT_ODDS_THRESHOLD,
    }

    return default_state


def update_bookmaker(val: str, s: State):
    bk = val.split(" - ")[0]
    s["bookmaker"] = bk
    return s


def update_deviation(val: int, s: State):
    s["deviation"] = val
    return s


def update_odds_slider(val: float, s: State):
    s["odds_threshold"] = val
    return s


def check_auth(username, password):
    if APP_ENV == "dev":
        return True

    return username == "bet" and password == UI_PASSWORD


def get_gradio_app():
    block = gr.Blocks(css="footer{display:none !important}")
    with block:
        # database Events that are used to create dataframe views
        fixtures = gr.State(value=[])

        state = gr.State(value=get_default_state())

        gr.Markdown("""Bets""")
        bk_dropdown = gr.Dropdown(
            get_bookmakers(),
            value=REFERENCE_BOOKMAKER,
            interactive=True,
            label="Reference bookmaker",
        )

        bk_dropdown.select(
            update_bookmaker,
            inputs=[bk_dropdown, state],
            outputs=[state],
        )

        with gr.Row():
            direction_dropdown = gr.Dropdown(
                ["lower", "higher", "both"],
                value="both",
                interactive=True,
                label="Deviation direction",
            )

            strategy_dropdown = gr.Dropdown(
                ["percent", "absolute"],
                value="percent",
                interactive=True,
                label="Deviation strategy",
            )

        with gr.Row():
            absolute_deviation_slider = gr.Slider(
                minimum=1,
                maximum=10,
                value=2,
                step=0.1,
                interactive=True,
                label="Absolute deviation threshold",
            )

            deviation_slider = gr.Slider(
                minimum=MINIMUM_DEVIATION,
                maximum=MAXIMUM_DEVIATION,
                value=DEFAULT_DEVIATION,
                step=1,
                interactive=True,
                label="Percent deviation threshold",
            )

            deviation_slider.change(
                update_deviation,
                inputs=[deviation_slider, state],
                outputs=[state],
            )

        odds_slider = gr.Slider(
            minimum=MINIMUM_ODDS_THRESHOLD,
            maximum=MAXIMUM_ODDS_THRESHOLD,
            value=DEFAULT_ODDS_THRESHOLD,
            step=0.10,
            interactive=True,
            label="Limit odds",
        )

        odds_slider.change(
            update_odds_slider,
            inputs=[odds_slider, state],
            outputs=[state],
        )

        with gr.Tabs():
            with gr.TabItem("Detail"):
                with gr.Row():
                    detail_data = gr.components.Dataframe(type="pandas")

            with gr.TabItem("Info"):
                with gr.Row():
                    info_data = gr.components.Dataframe(type="pandas")

        with gr.Tabs():
            with gr.TabItem("Events"):
                with gr.Row():
                    data = gr.components.Dataframe(type="pandas", interactive=False)
                    data.select(
                        event_on_select,
                        inputs=[data, fixtures, state],
                        outputs=detail_data,
                    )
                    data.select(
                        info_on_select,
                        inputs=[data, fixtures, state],
                        outputs=info_data,
                    )
                with gr.Row():
                    data_run = gr.Button("Refresh")
                    data_run.click(
                        fetch_events, inputs=[state], outputs=[fixtures, data]
                    )

        # running the function on page load in addition to when the button is clicked
        block.load(fetch_events, inputs=[state], outputs=[fixtures, data])

    return block


demo = get_gradio_app()

if __name__ == "__main__":
    demo.launch(auth=check_auth)
