from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "season" ADD "odds_coverage" BOOL;
        CREATE INDEX "idx_season_odds_co_3ee460" ON "season" ("odds_coverage");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_season_odds_co_3ee460";
        ALTER TABLE "season" DROP COLUMN "odds_coverage";"""
