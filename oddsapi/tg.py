import asyncio

from pyrogram import Client, filters, idle

from oddsapi.helpers import time_now
from .db import init_db, redis_connect
from .models import Notification
from .report import (
    filter_fixtures,
    get_table_fig,
    gen_img,
    get_unnotified_fixtures,
    get_cache_img,
)
from .settings import TG_BOT_NAME, TG_BOT_TOKEN, TG_API_ID, TG_API_HASH

app = Client(
    TG_BOT_NAME, bot_token=TG_BOT_TOKEN, api_id=TG_API_ID, api_hash=TG_API_HASH
)
CHAT_ID = "bet_monitor"


@app.on_message(filters.text & filters.private)
async def echo(client, message):
    photo = await get_cache_img(client.redis_connection)
    await message.reply_photo(photo=photo)


async def notify():
    fixtures = await get_unnotified_fixtures()
    if not fixtures:
        return

    notifications = []
    for fixture in fixtures:
        n = Notification()
        n.fixture = fixture
        n.platform = "telegram"

        date = fixture.date.strftime("%d %b. %H:%M:%S")
        n.message = f"{fixture.home_team_name} VS {fixture.away_team_name} - {date}"
        notifications.append(n)

    messages = [notification.message for notification in notifications]
    msg = "\n\n".join(messages)

    fig = get_table_fig(fixtures)
    photo = gen_img(fig)

    async with app:
        await app.send_photo(chat_id=CHAT_ID, caption=msg, photo=photo)

    for notification in notifications:
        notification.sent_at = time_now()
        await notification.save()


async def async_main():
    await init_db()
    await notify()

    # start/stop pyrogram manually since there is no middleware for handling redis connection
    await app.start()
    app.redis_connection = await redis_connect()
    await idle()
    await app.redis_connection.close()
    await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    run = loop.run_until_complete(async_main())
