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
from oddsapi.ui.helpers import get_bookmakers, get_leagues, get_leagues_str

matplotlib.use("Agg")

import pandas as pd

MINIMUM_ODDS_THRESHOLD = 1.0
MAXIMUM_ODDS_THRESHOLD = 10.0

MINIMUM_ABSOLUTE_DEVIATION = 1.0
MAXIMUM_ABSOLUTE_DEVIATION = 10.0

MINIMUM_PERCENT_DEVIATION = 15
MAXIMUM_PERCENT_DEVIATION = 60

# globals (meh)
leagues = get_leagues(REFERENCE_BOOKMAKER)
bookmakers = get_bookmakers()


def get_fixtures(param_state: dict):
    # leagues
    selected_league_ids = []
    for league_index in param_state["league_indexes"]:
        selected_league_ids.append(leagues[league_index].id)

    params = FixtureQueryParams(
        percent_deviation_threshold=param_state["percent_deviation"],
        absolute_deviation_threshold=param_state["absolute_deviation"],
        max_odds=param_state["odds_threshold"],
        reference_bookmaker=param_state["reference_bookmaker"],
        deviation_strategy=param_state["deviation_strategy"],
        deviation_direction=param_state["deviation_direction"],
        all_bets_must_match=param_state["all_bets_must_match"],
        league_ids=selected_league_ids,
    )

    async def async_get_data():
        async with SessionLocal() as session:
            f = await find_filtered_fixtures(session, params)
            return f

    return asyncio.run(async_get_data())


def fetch_events(
    param_state: dict,
):
    fxs = get_fixtures(param_state)

    event_data = []

    for fixture in fxs:
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
    return fxs, df


# display the odds for a given fixture on select
def event_on_select(evt: gr.SelectData, df: DataFrame, fxs: list, param_state: dict):
    row_id = evt.index[0]
    fixture_id = df.iloc[row_id]["Id"]

    fixture = next((f for f in fxs if f.id == fixture_id), None)

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
        d for d in odds_data if d["Bookmaker"] == param_state["reference_bookmaker"]
    ]

    # filter the dictionaries where "Bookmaker" is not equal to "mybk"
    other_bk_odds = [
        d for d in odds_data if d["Bookmaker"] != param_state["reference_bookmaker"]
    ]

    # create a dataframe from the filtered dictionaries
    df = pd.DataFrame(reference_bk_odds + other_bk_odds)

    return df


# display the odds for a given fixture on select
def info_on_select(evt: gr.SelectData, df_data: DataFrame, fxs: list):
    row_id = evt.index[0]
    fixture_id = df_data.iloc[row_id]["Id"]

    fixture = next((f for f in fxs if f.id == fixture_id), None)

    if fixture is None:
        return None

    # create a dataframe with the odds for the selected fixture
    df_data = {
        "Source update": fixture.source_update,
        "Date": fixture.date,
        "Away_team_logo": fixture.away_team_logo,
    }

    df = pd.DataFrame([df_data])

    return df


def get_default_state() -> dict:
    default_state = {
        "reference_bookmaker": REFERENCE_BOOKMAKER,
        "deviation_direction": DEFAULT_DEVIATION_DIRECTION,
        "deviation_strategy": DEFAULT_DEVIATION_STRATEGY,
        "odds_threshold": DEFAULT_ODDS_THRESHOLD,
        "percent_deviation": DEFAULT_PERCENT_DEVIATION,
        "absolute_deviation": DEFAULT_ABSOLUTE_DEVIATION,
        "all_bets_must_match": True,
        "league_indexes": [],
    }

    return default_state


def update_reference_bookmaker(val: str, s: State):
    bk = val.split(" - ")[0]
    s["reference_bookmaker"] = bk

    update = gr.Dropdown.update(choices=get_leagues_str(get_leagues(bk)))

    return s, update


def update_league(val: list[int], s: State):
    s["league_indexes"] = val
    return s


def update_strategy(val: str, s: State):
    s["deviation_strategy"] = val
    return s


def update_deviation_direction(val: str, s: State):
    s["deviation_direction"] = val
    return s


def update_all_bets_must_match(val: bool, s: State):
    s["all_bets_must_match"] = val
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


block = gr.Blocks(css="footer{display:none !important}")
with block:
    # database Events that are used to create dataframe views
    fixtures = gr.State(value=[])

    state = gr.State(value=get_default_state())

    gr.Markdown("""Bets""")

    with gr.Row():
        bk_dropdown = gr.Dropdown(
            bookmakers,
            value=REFERENCE_BOOKMAKER,
            interactive=True,
            label="Reference bookmaker",
        )

        all_bets_must_match = gr.Checkbox(
            label="All bets must match",
            value=True,
        )

    league_dropdown = gr.Dropdown(
        choices=get_leagues_str(leagues),
        value=None,
        interactive=True,
        multiselect=True,
        max_choices=5,
        type="index",
        label="League",
    )

    with gr.Row():
        direction_dropdown = gr.Dropdown(
            # take the keys from the enum
            [s.value for s in DeviationDirection],
            value=DEFAULT_DEVIATION_DIRECTION,
            interactive=True,
            label="Deviation direction",
        )

        strategy_dropdown = gr.Dropdown(
            # take the keys from the enum
            [s.value for s in DeviationStrategy],
            value=DEFAULT_DEVIATION_STRATEGY,
            interactive=True,
            label="Deviation strategy",
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

        percent_deviation_slider = gr.Slider(
            minimum=MINIMUM_PERCENT_DEVIATION,
            maximum=MAXIMUM_PERCENT_DEVIATION,
            value=DEFAULT_PERCENT_DEVIATION,
            step=1,
            interactive=True,
            label="Percent deviation threshold",
        )

    odds_slider = gr.Slider(
        minimum=MINIMUM_ODDS_THRESHOLD,
        maximum=MAXIMUM_ODDS_THRESHOLD,
        value=DEFAULT_ODDS_THRESHOLD,
        step=0.10,
        interactive=True,
        label="Limit odds",
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
                fixture_data = gr.components.Dataframe(type="pandas", interactive=False)

            data_run = gr.Button("Refresh")

    # event listeners
    fixture_data.select(
        event_on_select,
        inputs=[fixture_data, fixtures, state],
        outputs=detail_data,
    )
    fixture_data.select(
        info_on_select,
        inputs=[fixture_data, fixtures],
        outputs=info_data,
    )

    data_run.click(fetch_events, inputs=[state], outputs=[fixtures, fixture_data])

    bk_dropdown.select(
        update_reference_bookmaker,
        inputs=[bk_dropdown, state],
        outputs=[state, league_dropdown],
    )

    all_bets_must_match.select(
        update_all_bets_must_match,
        inputs=[all_bets_must_match, state],
        outputs=[state],
    )

    league_dropdown.select(
        update_league,
        inputs=[league_dropdown, state],
        outputs=[state],
    )

    direction_dropdown.select(
        update_deviation_direction,
        inputs=[direction_dropdown, state],
        outputs=[state],
    )

    strategy_dropdown.select(
        update_strategy,
        inputs=[strategy_dropdown, state],
        outputs=[state],
    )

    absolute_deviation_slider.change(
        update_absolute_deviation,
        inputs=[absolute_deviation_slider, state],
        outputs=[state],
    )

    percent_deviation_slider.change(
        update_percent_deviation,
        inputs=[percent_deviation_slider, state],
        outputs=[state],
    )

    odds_slider.change(
        update_odds_slider,
        inputs=[odds_slider, state],
        outputs=[state],
    )

    # running the function on page load in addition to when the button is clicked
    block.load(fetch_events, inputs=[state], outputs=[fixtures, fixture_data])

if __name__ == "__main__":
    block.launch(auth=check_auth)
