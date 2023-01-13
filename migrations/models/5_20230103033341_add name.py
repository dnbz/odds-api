from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "country" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(255),
    "code" VARCHAR(255),
    "flag" VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS "idx_country_created_8370f6" ON "country" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_country_updated_baa4a5" ON "country" ("updated_at");;
        ALTER TABLE "league" DROP COLUMN "country";
        ALTER TABLE "league" DROP COLUMN "country_code";
        CREATE TABLE IF NOT EXISTS "team" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(255),
    "founded_at" INT,
    "code" VARCHAR(255),
    "national" BOOL,
    "logo" VARCHAR(255),
    "country_id" INT REFERENCES "country" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_team_created_09b016" ON "team" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_team_updated_d9af3b" ON "team" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_team_founded_6ee950" ON "team" ("founded_at");
CREATE INDEX IF NOT EXISTS "idx_team_country_9985b4" ON "team" ("country_id");;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "league" ADD "country" VARCHAR(255);
        ALTER TABLE "league" ADD "country_code" VARCHAR(255);
        DROP TABLE IF EXISTS "team";
        DROP TABLE IF EXISTS "country";"""
