from pyrogram import Client

from oddsapi.settings import TG_BOT_NAME, TG_BOT_TOKEN, TG_API_ID, TG_API_HASH


def create_tgclient():
    client = Client(
        TG_BOT_NAME, bot_token=TG_BOT_TOKEN, api_id=TG_API_ID, api_hash=TG_API_HASH
    )

    return client
