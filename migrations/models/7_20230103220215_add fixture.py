from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "bookmaker" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        CREATE TABLE IF NOT EXISTS "fixture" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "source_id" INT NOT NULL,
    "timezone" VARCHAR(255),
    "date" TIMESTAMPTZ,
    "source_update" TIMESTAMPTZ,
    "league_season" INT,
    "away_team_id" INT REFERENCES "team" ("id"),
    "home_team_id" INT REFERENCES "team" ("id"),
    "league_id" INT REFERENCES "league" ("id")
);
CREATE INDEX IF NOT EXISTS "idx_fixture_created_3d13cb" ON "fixture" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_fixture_updated_8810f0" ON "fixture" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_fixture_source__8c5938" ON "fixture" ("source_id");
CREATE INDEX IF NOT EXISTS "idx_fixture_date_5e8846" ON "fixture" ("date");
CREATE INDEX IF NOT EXISTS "idx_fixture_league__403051" ON "fixture" ("league_season");
CREATE INDEX IF NOT EXISTS "idx_fixture_away_te_7b14bd" ON "fixture" ("away_team_id");
CREATE INDEX IF NOT EXISTS "idx_fixture_home_te_d175c6" ON "fixture" ("home_team_id");
CREATE INDEX IF NOT EXISTS "idx_fixture_league__32765b" ON "fixture" ("league_id");;
        ALTER TABLE "league" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "team" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "team" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "league" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "season" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "country" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "created_at" TYPE TIMESTAMPTZ USING "created_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        ALTER TABLE "bookmaker" ALTER COLUMN "updated_at" TYPE TIMESTAMPTZ USING "updated_at"::TIMESTAMPTZ;
        DROP TABLE IF EXISTS "fixture";"""
