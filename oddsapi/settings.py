#!/usr/bin/env python3
import os

from dotenv import load_dotenv

load_dotenv()

# bookmakers that are parsed from apifootball. legacy setting
APIFOOTBALL_BOOKMAKERS = ["Marathonbet", "Pinnacle"]

# access dsn for sentry error reporting
SENTRY_DSN = os.environ.get("SENTRY_DSN")

UI_PASSWORD = os.environ.get("UI_PASSWORD")

# сколько дней ставок загружать
BET_PARSE_DAYS = 12
# сколько дней матчей загружать
FIXTURE_PARSE_DAYS = 31

# настройки фильтров для ставок
# отклонение от среднего
DEVIATION_THRESHOLD = 20
# максимальный коэффициент. Если коэффициент больше, то ставка не учитывается
MAX_ODDS = 6.5
# референсный букмекер. Отображаются только события, которые есть у этого букмекера
REFERENCE_BOOKMAKER = "fonbet"

APP_ENV = os.environ.get("APP_ENV", default="prod")

API_HOST = "api-football-v1.p.rapidapi.com"
API_URL = f"https://{API_HOST}/v3"
API_KEY = os.environ.get("APIFOOTBALL_KEY")

TG_API_ID = os.environ.get("TG_API_ID")
TG_API_HASH = os.environ.get("TG_API_HASH")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_BOT_NAME = os.environ.get("TG_BOT_NAME")
TG_CHANNEL = os.environ.get("TG_CHANNEL")

DISABLE_PROXY = os.environ.get("DISABLE_PROXY", default=False)

if os.environ.get("DB_ECHO"):
    DB_ECHO = True
else:
    DB_ECHO = False

REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

HTTPX_PROXY = os.environ.get("HTTPX_PROXY")

DATABASE_CONNECTION = os.environ.get(
    "DATABASE_CONNECTION",
    default="postgresql://postgres:mypassword@localhost:5432/oddsapi",
)
