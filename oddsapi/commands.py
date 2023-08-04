import asyncio

import sentry_sdk
import uvloop

from oddsapi.database.clean import clean_notify, clean_matches, clean_static, clean_all
from oddsapi.helpers import configure_logging
from oddsapi.apifootball.loader import load_static, load_matches, autoimport
from oddsapi.parser_import.listener import (
    PinnacleListener,
    MarathonListener,
    FonbetListener,
    BetcityListener,
)
from oddsapi.settings import SENTRY_DSN
from oddsapi.tgbot.tgbot import run_tg_notify, tgbot

configure_logging()
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )


def import_matches():
    asyncio.run(load_matches())


def import_static():
    asyncio.run(load_static())


def import_autoimport():
    asyncio.run(autoimport())


def betcity_listener(debug: bool = False):
    listener = BetcityListener(debug=debug)
    asyncio.run(listener.start())


def fonbet_listener(debug: bool = False):
    listener = FonbetListener(debug=debug)
    asyncio.run(listener.start())


def pinnacle_listener(debug: bool = False):
    listener = PinnacleListener(debug=debug)
    asyncio.run(listener.start())


def marathon_listener(debug: bool = False):
    listener = MarathonListener(debug=debug)
    asyncio.run(listener.start())


def delete_notify():
    asyncio.run(clean_notify())


def delete_static():
    asyncio.run(clean_static())


def delete_matches():
    asyncio.run(clean_matches())


def delete_all():
    asyncio.run(clean_all())


def telegram_notify():
    asyncio.run(run_tg_notify())


def run_tgbot():
    asyncio.run(tgbot())
