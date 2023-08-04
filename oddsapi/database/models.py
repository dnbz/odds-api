from datetime import datetime

from sqlalchemy import (
    Integer,
    DateTime,
    text,
    String,
    Numeric,
    ForeignKey,
    Text,
    Boolean,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship, query_expression

from oddsapi.database.init import Base


class Bet(Base):
    __tablename__ = "bet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    source: Mapped[str] = mapped_column(String(255), index=True)
    event_url: Mapped[str] = mapped_column(String(511), index=True, nullable=True)
    source_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    source_update: Mapped[datetime] = mapped_column(
        DateTime(True), default=text("CURRENT_TIMESTAMP"), index=True, nullable=True
    )
    bookmaker: Mapped[str] = mapped_column(String(255), index=True)
    home_win: Mapped[float] = mapped_column(Numeric(12, 6), index=True, nullable=True)
    away_win: Mapped[float] = mapped_column(Numeric(12, 6), index=True, nullable=True)
    draw: Mapped[float] = mapped_column(Numeric(12, 6), index=True, nullable=True)

    fixture_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fixture.id"), index=True
    )
    fixture: Mapped["Fixture"] = relationship("Fixture", back_populates="bets")

    outcomes: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=True)
    first_half_outcomes: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )
    # jsonb with gin index
    totals: Mapped[dict] = mapped_column(MutableList.as_mutable(JSONB), nullable=True)

    handicaps: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )

    __table_args__ = (
        Index("idx_gin_totals", totals, postgresql_using="gin"),
        Index("idx_gin_handicaps", handicaps, postgresql_using="gin"),
        Index("idx_gin_outcomes", outcomes, postgresql_using="gin"),
        Index(
            "idx_gin_first_half_outcomes", first_half_outcomes, postgresql_using="gin"
        ),
    )


class Bookmaker(Base):
    __tablename__ = "bookmaker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
        onupdate=func.now(),
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), index=True)


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
        onupdate=func.now(),
    )

    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(255), nullable=True)
    flag: Mapped[str] = mapped_column(String(255), nullable=True)

    teams: Mapped[list["Team"]] = relationship("Team", back_populates="country")


class Fixture(Base):
    __tablename__ = "fixture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
        onupdate=func.now(),
    )

    source_update: Mapped[datetime] = mapped_column(
        DateTime(True), index=True, nullable=True
    )

    timezone: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(DateTime(True), index=True)

    league_season: Mapped[int] = mapped_column(Integer)

    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("league.id"), index=True)
    league: Mapped["League"] = relationship("League", back_populates="fixtures")

    bets: Mapped[list["Bet"]] = relationship("Bet", back_populates="fixture")
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="fixture"
    )

    away_team_logo: Mapped[str] = mapped_column(String(255))
    away_team_source_id: Mapped[int] = mapped_column(Integer, index=True)
    away_team_name: Mapped[str] = mapped_column(String(255), index=True)
    away_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("team.id"), index=True, nullable=True
    )
    away_team: Mapped["Team"] = relationship(
        "Team", back_populates="away_fixtures", foreign_keys=[away_team_id]
    )

    home_team_logo: Mapped[str] = mapped_column(String(255))
    home_team_source_id: Mapped[int] = mapped_column(Integer, index=True)
    home_team_name: Mapped[str] = mapped_column(String(255), index=True)
    home_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("team.id"), index=True, nullable=True
    )
    home_team: Mapped["Team"] = relationship(
        "Team", back_populates="home_fixtures", foreign_keys=[home_team_id]
    )

    # conditions which indicate which odds have been matched to a fixture
    trigger: Mapped[str] = query_expression()
    condition_away_win: Mapped[bool] = query_expression()
    condition_home_win: Mapped[bool] = query_expression()
    condition_draw: Mapped[bool] = query_expression()

    def get_conditions(self) -> dict:
        return {
            "away_win": self.condition_away_win,
            "home_win": self.condition_home_win,
            "draw": self.condition_draw,
        }


class League(Base):
    __tablename__ = "league"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
        onupdate=func.now(),
    )

    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255))
    logo: Mapped[str] = mapped_column(String(255))

    seasons: Mapped[list["Season"]] = relationship("Season", back_populates="league")
    fixtures: Mapped[list["Fixture"]] = relationship("Fixture", back_populates="league")

    fixture_count: Mapped[int] = query_expression()


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        default=func.now(),
        index=True,
        onupdate=func.now(),
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(True), index=True)
    platform: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)

    fixture_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fixture.id"), index=True
    )
    fixture: Mapped["Fixture"] = relationship("Fixture", back_populates="notifications")


class Season(Base):
    __tablename__ = "season"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
        onupdate=func.now(),
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    start: Mapped[datetime] = mapped_column(DateTime(True), index=True)
    end: Mapped[datetime] = mapped_column(DateTime(True), index=True)

    current: Mapped[bool] = mapped_column(Boolean, index=True)
    odds_coverage: Mapped[bool] = mapped_column(Boolean, index=True)

    league_id = mapped_column(
        Integer, ForeignKey("league.id"), nullable=False, index=True
    )
    league: Mapped["League"] = relationship("League", back_populates="seasons")


class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True),
        nullable=False,
        index=True,
        default=func.now(),
        onupdate=func.now(),
    )

    founded_at: Mapped[int] = mapped_column(Integer, index=True, nullable=True)

    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(255), nullable=True)
    logo: Mapped[str] = mapped_column(String(255), nullable=True)

    national: Mapped[bool] = mapped_column(Boolean)

    country_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("country.id"), index=True
    )

    country: Mapped["Country"] = relationship("Country", back_populates="teams")

    home_fixtures: Mapped[list["Fixture"]] = relationship(
        "Fixture",
        foreign_keys="Fixture.home_team_id",
        back_populates="home_team",
    )
    away_fixtures: Mapped[list["Fixture"]] = relationship(
        "Fixture",
        foreign_keys="Fixture.away_team_id",
        back_populates="away_team",
    )
