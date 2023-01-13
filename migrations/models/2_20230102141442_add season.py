from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "league" ADD "updated_at" TIMESTAMPTZ NOT NULL;
        ALTER TABLE "league" ADD "created_at" TIMESTAMPTZ NOT NULL;
        CREATE TABLE IF NOT EXISTS "season" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "year" INT NOT NULL,
    "start" TIMESTAMPTZ NOT NULL,
    "end" TIMESTAMPTZ NOT NULL,
    "current" BOOL,
    "league_id" INT NOT NULL REFERENCES "league" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_season_created_e3bd10" ON "season" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_season_updated_b02e0e" ON "season" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_season_year_7726f0" ON "season" ("year");
CREATE INDEX IF NOT EXISTS "idx_season_start_58cf38" ON "season" ("start");
CREATE INDEX IF NOT EXISTS "idx_season_end_b4b29b" ON "season" ("end");
CREATE INDEX IF NOT EXISTS "idx_season_current_8e3d77" ON "season" ("current");
CREATE INDEX IF NOT EXISTS "idx_season_league__0d9e8d" ON "season" ("league_id");;
        CREATE INDEX "idx_league_updated_9b2f3c" ON "league" ("updated_at");
        CREATE INDEX "idx_league_created_5c176e" ON "league" ("created_at");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_league_created_5c176e";
        DROP INDEX "idx_league_updated_9b2f3c";
        ALTER TABLE "league" DROP COLUMN "updated_at";
        ALTER TABLE "league" DROP COLUMN "created_at";
        DROP TABLE IF EXISTS "season";"""
