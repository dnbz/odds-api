import asyncio
import logging
from datetime import datetime

from tortoise.expressions import Q

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
