from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "fixture" ADD "home_team_logo" VARCHAR(255);
        ALTER TABLE "fixture" ADD "away_team_logo" VARCHAR(255);
        ALTER TABLE "fixture" ADD "away_team_source_id" INT;
        ALTER TABLE "fixture" ADD "home_team_source_id" INT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "fixture" DROP COLUMN "home_team_logo";
        ALTER TABLE "fixture" DROP COLUMN "away_team_logo";
        ALTER TABLE "fixture" DROP COLUMN "away_team_source_id";
        ALTER TABLE "fixture" DROP COLUMN "home_team_source_id";"""
