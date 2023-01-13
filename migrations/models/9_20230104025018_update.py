from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "fixture" ADD "away_team_name" VARCHAR(255);
        ALTER TABLE "fixture" ADD "home_team_name" VARCHAR(255);
        CREATE INDEX "idx_fixture_away_te_7d8774" ON "fixture" ("away_team_name");
        CREATE INDEX "idx_fixture_home_te_3efc2f" ON "fixture" ("home_team_name");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_fixture_home_te_3efc2f";
        DROP INDEX "idx_fixture_away_te_7d8774";
        ALTER TABLE "fixture" DROP COLUMN "away_team_name";
        ALTER TABLE "fixture" DROP COLUMN "home_team_name";"""
