import logging

from pyrogram import Client
from pyrogram.raw import functions
from pyrogram.raw.types import Config
from sqlalchemy.ext.asyncio import AsyncSession

from oddsapi.database.models import Fixture, Notification
from oddsapi.helpers import time_now
from oddsapi.settings import TG_CHANNEL
from oddsapi.tgbot.tg_report import gen_img_from_fixtures


async def bulk_send_notifications(
    fixtures: list[Fixture], app: Client, session: AsyncSession
):
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

    limit = await get_caption_length_limit(app)

    if len(msg) > limit:
        msg = msg[: limit - 3] + "..."
        logging.warning(
            f"caption for the notification message too long, truncated to {limit} characters"
        )

    photo = gen_img_from_fixtures(fixtures)

    # print("sending photo")
    await app.send_photo(chat_id=TG_CHANNEL, caption=msg, photo=photo)
    # await app.send_message(chat_id=TG_CHANNEL, text=msg)
    # print("sent photo")

    for notification in notifications:
        notification.sent_at = time_now()

    session.add_all(notifications)
    await session.commit()


async def get_caption_length_limit(app: Client):
    conf: Config = await app.invoke(functions.help.GetConfig())
    limit = conf.caption_length_max
    return limit
