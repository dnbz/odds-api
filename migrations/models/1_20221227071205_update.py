from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "league" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "source_id" INT NOT NULL,
    "country" VARCHAR(255),
    "country_code" VARCHAR(255),
    "name" VARCHAR(255),
    "type" VARCHAR(255),
    "logo" VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS "idx_league_source__5d382e" ON "league" ("source_id");;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "league";"""
