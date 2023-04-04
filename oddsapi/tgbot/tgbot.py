from pyrogram import Client, filters, idle

from oddsapi.database.init import SessionLocal
from oddsapi.filter.fixture import find_filtered_fixtures, find_unnotified_fixtures
from oddsapi.tgbot.connect import create_tgclient
from oddsapi.tgbot.tg_report import get_cache_img
from oddsapi.tgbot.tg_notify import bulk_send_notifications
from oddsapi.database.redis_connection import redis_connect


async def tg_notify(app: Client):
    async with SessionLocal() as session:
        fixtures = await find_unnotified_fixtures(session)
        if fixtures:
            await bulk_send_notifications(fixtures=fixtures, app=app, session=session)


async def run_tg_notify():
    tg_client = create_tgclient()
    await tg_client.start()
    await tg_notify(tg_client)
    await tg_client.stop()


async def tgbot():
    tg_client = create_tgclient()

    @tg_client.on_message(filters.text & filters.private)
    async def echo(client, message):
        fixtures = await find_filtered_fixtures(client.dbsession)
        print(f"found {len(fixtures)} fixtures")
        photo = await get_cache_img(client.redis_connection, fixtures)
        photo.name = "photo.png"
        await message.reply_document(document=photo)

    # start/stop pyrogram manually since there is no middleware for handling redis connection
    await tg_client.start()
    tg_client.redis_connection = await redis_connect()
    tg_client.dbsession = SessionLocal()
    await idle()
    await tg_client.dbsession.close()
    await tg_client.redis_connection.close()
    await tg_client.stop()
