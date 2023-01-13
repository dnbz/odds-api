from tortoise.models import Model
from tortoise import fields


class League(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)
    source_id = fields.IntField(index=True)
    name = fields.CharField(max_length=255, null=True)
    type = fields.CharField(max_length=255, null=True)
    logo = fields.CharField(max_length=255, null=True)

    seasons: fields.ReverseRelation["Season"]

    def __str__(self):
        return self.name


class Season(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    year = fields.IntField(index=True)
    start = fields.DatetimeField(index=True, null=True)
    end = fields.DatetimeField(index=True, null=True)
    current = fields.BooleanField(null=True, index=True)

    odds_coverage = fields.BooleanField(null=True, index=True)

    league: fields.ForeignKeyRelation["League"] = fields.ForeignKeyField(
        "models.League", related_name="seasons", index=True
    )


class Country(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    name = fields.CharField(max_length=255, null=True)
    code = fields.CharField(max_length=255, null=True)
    flag = fields.CharField(max_length=255, null=True)

    teams: fields.ReverseRelation["Team"]


class Team(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    source_id = fields.IntField(index=True)
    founded_at = fields.IntField(index=True, null=True)
    name = fields.CharField(max_length=255, null=True)
    code = fields.CharField(max_length=255, null=True)
    national = fields.BooleanField(null=True)
    logo = fields.CharField(max_length=255, null=True)

    country: fields.ForeignKeyRelation["Country"] = fields.ForeignKeyField(
        "models.Country", related_name="teams", index=True, null=True
    )


class Bookmaker(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    name = fields.CharField(max_length=255, null=True)
    source_id = fields.IntField(index=True)


class Fixture(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    source_id = fields.IntField(index=True)

    timezone = fields.CharField(max_length=255, null=True)
    date = fields.DatetimeField(max_length=255, null=True, index=True)
    source_update = fields.DatetimeField(max_length=255, null=True)

    home_team_name = fields.CharField(max_length=255, index=True, null=True)
    away_team_name = fields.CharField(max_length=255, index=True, null=True)

    home_team_logo = fields.CharField(max_length=255, null=True)
    away_team_logo = fields.CharField(max_length=255, null=True)

    home_team_source_id = fields.IntField(null=True)
    away_team_source_id = fields.IntField(null=True)

    league_season = fields.IntField(index=True, null=True)

    bets: fields.ReverseRelation["Bet"]

    notifications: fields.ReverseRelation["Notification"]

    league: fields.ForeignKeyRelation["League"] = fields.ForeignKeyField(
        "models.League", related_name="fixtures", index=True, null=True
    )

    home_team: fields.ForeignKeyRelation["Team"] = fields.ForeignKeyField(
        "models.Team", related_name="fixtures_home", index=True, null=True
    )

    away_team: fields.ForeignKeyRelation["Team"] = fields.ForeignKeyField(
        "models.Team", related_name="fixtures_away", index=True, null=True
    )


class Bet(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    source = fields.CharField(max_length=255, null=True)
    source_id = fields.IntField(index=True, null=True)
    source_update = fields.DatetimeField(index=True, auto_now=True, null=True)

    bookmaker = fields.CharField(max_length=255, null=True)

    home_win = fields.DecimalField(
        max_digits=12, decimal_places=6, index=True, null=True
    )
    away_win = fields.DecimalField(
        max_digits=12, decimal_places=6, index=True, null=True
    )
    draw = fields.DecimalField(max_digits=12, decimal_places=6, index=True, null=True)

    total_under25 = fields.DecimalField(
        max_digits=12, decimal_places=6, index=True, null=True
    )
    total_over25 = fields.DecimalField(
        max_digits=12, decimal_places=6, index=True, null=True
    )

    fixture: fields.ForeignKeyRelation["Fixture"] = fields.ForeignKeyField(
        "models.Fixture", related_name="bets", index=True, null=True
    )


class Notification(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(index=True, auto_now_add=True)
    updated_at = fields.DatetimeField(index=True, auto_now=True)

    sent_at = fields.DatetimeField(index=True, null=True)

    platform = fields.CharField(max_length=255, null=True, index=True)
    message = fields.TextField(null=True)

    fixture: fields.ForeignKeyRelation["Fixture"] = fields.ForeignKeyField(
        "models.Fixture", related_name="notifications", index=True, null=True
    )
