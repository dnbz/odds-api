from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "season" ALTER COLUMN "start" DROP NOT NULL;
        ALTER TABLE "season" ALTER COLUMN "end" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "season" ALTER COLUMN "start" SET NOT NULL;
        ALTER TABLE "season" ALTER COLUMN "end" SET NOT NULL;"""
