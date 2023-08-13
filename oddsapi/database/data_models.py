from dataclasses import dataclass
from typing import Optional


@dataclass
class TotalOdds:
    total: str
    total_under: str
    total_over: str


@dataclass
class HandicapOdds:
    handicap: str
    coef: str
    type: str


@dataclass
class OutcomeOdds:
    draw: str
    home_win: str
    away_win: str


@dataclass(slots=False)
class CommonEvent:
    event_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    handicap_odds: object | None
    total_odds: list[TotalOdds] | None
    first_half_outcome_odds: OutcomeOdds | None
    outcome_odds: OutcomeOdds
    name: Optional[str] = None


@dataclass(slots=False)
class BetcityEvent:
    event_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    handicap_odds: object | None
    total_odds: list[TotalOdds] | None
    first_half_outcome_odds: OutcomeOdds | None
    outcome_odds: OutcomeOdds
    name: Optional[str] = None


@dataclass(slots=False)
class FonbetEvent:
    event_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    handicap_odds: object | None
    total_odds: list[TotalOdds] | None
    first_half_outcome_odds: OutcomeOdds | None
    outcome_odds: OutcomeOdds
    name: Optional[str] = None


@dataclass(slots=False)
class PinnacleEvent:
    event_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    handicap_odds: dict | None
    total_odds: list | None
    first_half_outcome_odds: OutcomeOdds | None
    outcome_odds: OutcomeOdds
    name: Optional[str] = None


@dataclass(slots=False)
class MarathonEvent:
    event_url: str
    datetime: str
    home_team_name: str
    away_team_name: str
    handicap_odds: dict | None
    total_odds: list | None
    first_half_outcome_odds: OutcomeOdds | None
    outcome_odds: OutcomeOdds
    name: Optional[str] = None
