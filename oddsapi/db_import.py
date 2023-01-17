import asyncio
import logging
import pytz
from dataclasses import dataclass
from datetime import datetime, timedelta

from tortoise.expressions import Q

from .helpers import time_now
from .models import League, Season, Country, Team, Bookmaker, Fixture, Bet


async def add_country(country: dict):
    update = True
    c = await Country.filter(name=country["name"]).first()

    if not c:
        update = False
        c = Country()
        c.name = country["name"]

    c.code = country["code"]
    c.flag = country["flag"]

    await c.save()


async def add_bet(data: dict, bookmaker: dict):
    fixture_id = data["fixture"]["id"]
    fixture = await Fixture.filter(source_id=fixture_id).first()

    if not fixture:
        logging.warning(f"Fixture with id {fixture_id} not found for bet.")

    update = True
    b = await Bet.filter(
        Q(fixture_id=fixture.id), Q(bookmaker=bookmaker["name"])
    ).first()
    if not b:
        update = False
        b = Bet()
        b.fixture = fixture
        b.bookmaker = bookmaker["name"]

    b.source = "apifootball"
    b.source_update = datetime.fromisoformat(data["update"])

    # https://www.api-football.com/documentation-v3#tag/Odds-(Pre-Match)/operation/get-odds
    for bet in bookmaker["bets"]:
        if bet.get("name") == "Match Winner":
            b.home_win = float(bet["values"][0]["odd"])
            b.draw = float(bet["values"][1]["odd"])
            b.away_win = float(bet["values"][2]["odd"])

        elif bet.get("name") == "Goals Over/Under":
            for total in bet["values"]:
                if total.get("value") == "Over 2.5":
                    b.total_over25 = float(total["odd"])
                elif total.get("value") == "Under 2.5":
                    b.total_under25 = float(total["odd"])

    await b.save()


async def add_fixture(data: dict):
    fixture = data["fixture"]
    league = data["league"]
    home_team = data["teams"]["home"]
    away_team = data["teams"]["away"]

    update = True
    f = await Fixture.filter(source_id=fixture["id"]).first()
    if not f:
        update = False
        f = Fixture()
        f.source_id = fixture["id"]

    f.timezone = fixture["timezone"]
    f.date = datetime.fromisoformat(fixture["date"])

    f.league_season = league["season"]

    f.home_team_name = home_team["name"]
    f.home_team_logo = home_team["logo"]
    f.home_team_source_id = home_team["id"]

    f.away_team_name = away_team["name"]
    f.away_team_logo = away_team["logo"]
    f.away_team_source_id = away_team["id"]

    # don't update existing relations
    if not update:
        league_model = await League.filter(source_id=league["id"]).first()

        if league_model:
            f.league = league_model
        else:
            logging.warning(
                f"No league with id {league['id']} found for fixture {dict(f)}"
            )

        # home_team = await Team.filter(source_id=home_team['id']).first()
        # away_team = await Team.filter(source_id=away_team['id']).first()
        # f.home_team = home_team
        # f.away_team = away_team

    await f.save()


async def add_bookmaker(bookmaker: dict):
    b = await Bookmaker.filter(source_id=bookmaker["id"]).first()
    update = True
    if not b:
        update = False
        b = Bookmaker()
        b.source_id = bookmaker["id"]

    b.name = bookmaker["name"]

    await b.save()


async def add_team(team_data: dict, country_id: int):
    team = team_data["team"]

    t = await Team.filter(source_id=team["id"]).first()
    update = True
    if not t:
        update = False
        t = Team()
        t.source_id = team["id"]

    t.name = team["name"]
    t.code = team["code"]
    t.logo = team["logo"]
    t.founded_at = team["founded"]
    t.national = team["national"]

    t.country_id = country_id

    await t.save()


async def add_league(data: dict):
    league = data["league"]
    country = data["country"]
    seasons = data["seasons"]

    l = await League.filter(source_id=league["id"]).first()
    update = True
    if not l:
        update = False
        l = League()
        l.source_id = league["id"]

    l.country = country["name"]
    l.country_code = country["code"]
    l.country_flag = country["flag"]
    l.name = league["name"]
    l.type = league["type"]
    l.logo = league["logo"]

    await l.save()

    # logging.info(f"Refreshing seasons for league with id {l.id}")
    await l.seasons.all().delete()

    update_season_coros = [add_season(season, l) for season in seasons]

    await asyncio.gather(*update_season_coros)

    return len(update_season_coros)


async def add_season(season: dict, league: League):
    s = await Season.filter(Q(league_id=league.id), Q(year=season["year"])).first()
    update = True

    if not s:
        update = False
        s = Season()
        s.year = season["year"]
        s.league = league

    s.start = datetime.strptime(season["start"], "%Y-%m-%d")
    s.end = datetime.strptime(season["end"], "%Y-%m-%d")
    s.current = season["current"]

    if season.get("coverage"):
        s.odds_coverage = season["coverage"]["odds"]

    await s.save()


@dataclass(slots=False)
class BetcityEvent:
    event_url: str
    event_list_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    home_team: float
    draw: float
    away_team: float


async def add_betcity_bet(
    event: BetcityEvent, date: datetime, fixture: Fixture
) -> bool:
    await fixture.fetch_related("bets")

    b = None
    update = False
    for fixture_bet in fixture.bets:
        if fixture_bet.bookmaker == "betcity":
            logging.info(
                f"This betcity bet is already in db for fixture with id {fixture.id}. Updating..."
            )
            update = True
            b = fixture_bet

    five_min_ago = datetime.now() - timedelta(minutes=5)
    if (
        b is not None
        and (b.home_win != event.home_team)
        and (b.updated_at.replace(tzinfo=None) > five_min_ago)
    ):
        logging.warning(
            f"This betcity bet was modified less than five minutes ago"
            f" and now we are trying to update it with values different from previous one."
            f"This could be a bug."
        )

    if not b:
        update = False
        b = Bet()
        b.fixture = fixture
        b.bookmaker = "betcity"
        b.source = "betcity-parser"
        b.source_update = date

        logging.info(f"Adding bet from betcity for fixture with id {fixture.id}...")

    b.home_win = event.home_team
    b.draw = event.draw
    b.away_win = event.away_team

    # b.total_over25 = float(total["odd"])
    # b.total_under25 = float(total["odd"])

    await b.save()
    logging.log(
        5, f"imported bet for betcity wihh fixture id {fixture.id} successfully"
    )

    return update
