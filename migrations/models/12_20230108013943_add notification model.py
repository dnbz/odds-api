from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "notification" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "sent_at" TIMESTAMPTZ,
    "platform" VARCHAR(255),
    "message" TEXT,
    "fixture_id" INT REFERENCES "fixture" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_notificatio_created_0db009" ON "notification" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_notificatio_updated_91411c" ON "notification" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_notificatio_sent_at_e808e0" ON "notification" ("sent_at");
CREATE INDEX IF NOT EXISTS "idx_notificatio_platfor_3f24d0" ON "notification" ("platform");
CREATE INDEX IF NOT EXISTS "idx_notificatio_fixture_0a3330" ON "notification" ("fixture_id");;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "notification";"""
