#!/usr/bin/env python3
import os

from dotenv import load_dotenv

load_dotenv()

BOOKMAKERS = ["Marathonbet", "Pinnacle"]
# сколько дней ставок загружать
BET_PARSE_DAYS = 10
# сколько дней матчей загружать
FIXTURE_PARSE_DAYS = 31
DEVIATION_THRESHOLD = 10

APP_ENV = os.environ.get("APP_ENV", default="prod")

API_HOST = "api-football-v1.p.rapidapi.com"
API_URL = f"https://{API_HOST}/v3"
API_KEY = os.environ.get("APIFOOTBALL_KEY")


TG_API_ID = os.environ.get("TG_API_ID")
TG_API_HASH = os.environ.get("TG_API_HASH")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_BOT_NAME = os.environ.get("TG_BOT_NAME")

REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

DB_CONNECTION = os.environ.get(
    "DB_CONNECTION", default="postgresql://postgres:mypassword@localhost:5432/oddsapi"
)

TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": "postgres://postgres:Aif3eireuri6Ohriitohji2Oh@localhost:5478/oddsapi"
    },
    "apps": {
        "models": {
            "models": ["oddsapi.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
