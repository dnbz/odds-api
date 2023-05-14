import asyncio

import gradio as gr
import matplotlib
from gradio import State
from pandas import DataFrame

from oddsapi.database.init import SessionLocal
from oddsapi.filter.fixture import (
    find_filtered_fixtures,
    DeviationStrategy,
    DeviationDirection,
    DEFAULT_DEVIATION_STRATEGY,
    DEFAULT_DEVIATION_DIRECTION,
    DEFAULT_ODDS_THRESHOLD,
    DEFAULT_PERCENT_DEVIATION,
    FixtureQueryParams,
    DEFAULT_ABSOLUTE_DEVIATION,
)
from oddsapi.settings import (
    REFERENCE_BOOKMAKER,
    UI_PASSWORD,
    APP_ENV,
)
from oddsapi.ui.helpers import get_bookmakers, get_leagues

matplotlib.use("Agg")

import pandas as pd

MINIMUM_ODDS_THRESHOLD = 1.0
MAXIMUM_ODDS_THRESHOLD = 10.0

MINIMUM_ABSOLUTE_DEVIATION = 1.0
MAXIMUM_ABSOLUTE_DEVIATION = 10.0

MINIMUM_PERCENT_DEVIATION = 15
MAXIMUM_PERCENT_DEVIATION = 60

# globals (meh)
leagues = get_leagues()
bookmakers = get_bookmakers()


def get_fixtures(state: dict):
    # leagues
    selected_league_ids = []
    for league_index in state["league_indexes"]:
        selected_league_ids.append(leagues[league_index].id)

    params = FixtureQueryParams(
        percent_deviation_threshold=state["percent_deviation"],
        absolute_deviation_threshold=state["absolute_deviation"],
        max_odds=state["odds_threshold"],
        reference_bookmaker=state["reference_bookmaker"],
        deviation_strategy=state["deviation_strategy"],
        deviation_direction=state["deviation_direction"],
        league_ids=selected_league_ids,
    )

    async def async_get_data():
        async with SessionLocal() as session:
            f = await find_filtered_fixtures(session, params)
            return f

    fixtures = asyncio.run(async_get_data())
    return fixtures


def fetch_events(
    state: dict,
):
    fixtures = get_fixtures(state)

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
    # filter the dictionaries where "Bookmaker"
    reference_bk_odds = [
        d for d in odds_data if d["Bookmaker"] == state["reference_bookmaker"]
    ]

    # filter the dictionaries where "Bookmaker" is not equal to "mybk"
    other_bk_odds = [
        d for d in odds_data if d["Bookmaker"] != state["reference_bookmaker"]
    ]

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

    source_links = {f"{bet.source}": bet.source for bet in fixture.bets}

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
        "reference_bookmaker": REFERENCE_BOOKMAKER,
        "deviation_direction": DEFAULT_DEVIATION_DIRECTION,
        "deviation_strategy": DEFAULT_DEVIATION_STRATEGY,
        "odds_threshold": DEFAULT_ODDS_THRESHOLD,
        "percent_deviation": DEFAULT_PERCENT_DEVIATION,
        "absolute_deviation": DEFAULT_ABSOLUTE_DEVIATION,
        "league_indexes": [],
    }

    return default_state


def update_reference_bookmaker(val: str, s: State):
    bk = val.split(" - ")[0]
    s["reference_bookmaker"] = bk
    return s


def update_league(val: list[int], s: State):
    s["league_indexes"] = val
    return s


def update_strategy(val: str, s: State):
    s["deviation_strategy"] = val
    return s


def update_deviation_direction(val: str, s: State):
    s["deviation_direction"] = val
    return s


def update_percent_deviation(val: int, s: State):
    s["percent_deviation"] = val
    return s


def update_absolute_deviation(val: int, s: State):
    s["absolute_deviation"] = val
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
            bookmakers,
            value=REFERENCE_BOOKMAKER,
            interactive=True,
            label="Reference bookmaker",
        )

        bk_dropdown.select(
            update_reference_bookmaker,
            inputs=[bk_dropdown, state],
            outputs=[state],
        )

        # concatenate bookmaker names and count
        leagues_str = [f"{league.name} - {league.fixture_count}" for league in leagues]

        league_dropdown = gr.Dropdown(
            leagues_str,
            value=None,
            interactive=True,
            multiselect=True,
            max_choices=5,
            type="index",
            label="League",
        )

        league_dropdown.select(
            update_league,
            inputs=[league_dropdown, state],
            outputs=[state],
        )

        with gr.Row():
            direction_dropdown = gr.Dropdown(
                # take the keys from the enum
                [s.value for s in DeviationDirection],
                value=DEFAULT_DEVIATION_DIRECTION,
                interactive=True,
                label="Deviation direction",
            )

            direction_dropdown.select(
                update_deviation_direction,
                inputs=[direction_dropdown, state],
                outputs=[state],
            )

            strategy_dropdown = gr.Dropdown(
                # take the keys from the enum
                [s.value for s in DeviationStrategy],
                value=DEFAULT_DEVIATION_STRATEGY,
                interactive=True,
                label="Deviation strategy",
            )

            strategy_dropdown.select(
                update_strategy,
                inputs=[strategy_dropdown, state],
                outputs=[state],
            )

        with gr.Row():
            absolute_deviation_slider = gr.Slider(
                minimum=MINIMUM_ABSOLUTE_DEVIATION,
                maximum=MAXIMUM_ABSOLUTE_DEVIATION,
                value=DEFAULT_ABSOLUTE_DEVIATION,
                step=0.1,
                interactive=True,
                label="Absolute deviation threshold",
            )

            absolute_deviation_slider.change(
                update_absolute_deviation,
                inputs=[absolute_deviation_slider, state],
                outputs=[state],
            )

            percent_deviation_slider = gr.Slider(
                minimum=MINIMUM_PERCENT_DEVIATION,
                maximum=MAXIMUM_PERCENT_DEVIATION,
                value=DEFAULT_PERCENT_DEVIATION,
                step=1,
                interactive=True,
                label="Percent deviation threshold",
            )

            percent_deviation_slider.change(
                update_percent_deviation,
                inputs=[percent_deviation_slider, state],
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

                data_run = gr.Button("Refresh")
                data_run.click(fetch_events, inputs=[state], outputs=[fixtures, data])

        # running the function on page load in addition to when the button is clicked
        block.load(fetch_events, inputs=[state], outputs=[fixtures, data])

    return block


demo = get_gradio_app()

if __name__ == "__main__":
    demo.launch(auth=check_auth)
