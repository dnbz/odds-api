from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "bet" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "source" VARCHAR(255),
    "source_id" INT,
    "source_update" TIMESTAMPTZ   DEFAULT CURRENT_TIMESTAMP,
    "bookmaker" VARCHAR(255),
    "home_win" DOUBLE PRECISION,
    "away_win" DOUBLE PRECISION,
    "draw" DOUBLE PRECISION,
    "total_under25" DOUBLE PRECISION,
    "total_over25" DOUBLE PRECISION,
    "fixture_id" INT REFERENCES "fixture" ("id")
);
CREATE INDEX IF NOT EXISTS "idx_bet_created_f344f5" ON "bet" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_bet_updated_f6e1ac" ON "bet" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_bet_source__1608b2" ON "bet" ("source_id");
CREATE INDEX IF NOT EXISTS "idx_bet_source__24c11a" ON "bet" ("source_update");
CREATE INDEX IF NOT EXISTS "idx_bet_home_wi_b815ea" ON "bet" ("home_win");
CREATE INDEX IF NOT EXISTS "idx_bet_away_wi_1c20bf" ON "bet" ("away_win");
CREATE INDEX IF NOT EXISTS "idx_bet_draw_0c9ca9" ON "bet" ("draw");
CREATE INDEX IF NOT EXISTS "idx_bet_total_u_2ce3df" ON "bet" ("total_under25");
CREATE INDEX IF NOT EXISTS "idx_bet_total_o_2f9d29" ON "bet" ("total_over25");
CREATE INDEX IF NOT EXISTS "idx_bet_fixture_1ff527" ON "bet" ("fixture_id");;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "bet";"""
