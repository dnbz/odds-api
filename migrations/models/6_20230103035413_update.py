from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "bookmaker" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(255),
    "source_id" INT NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_bookmaker_created_e29208" ON "bookmaker" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_bookmaker_updated_619acc" ON "bookmaker" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_bookmaker_source__af144a" ON "bookmaker" ("source_id");;
        ALTER TABLE "team" ADD "source_id" INT NOT NULL;
        CREATE INDEX "idx_team_source__abcc0e" ON "team" ("source_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_team_source__abcc0e";
        ALTER TABLE "team" DROP COLUMN "source_id";
        DROP TABLE IF EXISTS "bookmaker";"""
