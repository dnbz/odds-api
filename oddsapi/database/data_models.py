from dataclasses import dataclass


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


@dataclass(slots=False)
class FonbetEvent:
    event_url: str
    name: str | None
    datetime: str
    home_team_name: str
    away_team_name: str
    home_team: float
    draw: float
    away_team: float


@dataclass(slots=False)
class PinnacleEvent:
    event_url: str
    event_list_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    home_team: float
    draw: float
    away_team: float


@dataclass(slots=False)
class MarathonEvent:
    event_url: str
    name: str | None
    datetime: str
    home_team_name: str
    away_team_name: str
    home_team: float
    draw: float
    away_team: float
