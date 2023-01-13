import asyncio
import json
from dataclasses import dataclass
from string import Template

from redis.asyncio import Redis

from oddsapi.db import redis_connect, RedisDB, init_db
from oddsapi.models import Fixture


@dataclass(slots=False)
class BetcityEvent:
    event_url: str
    event_list_url: str
    time: str
    home_team_name: str
    away_team_name: str
    home_team: float
    draw: float
    away_team: float


async def reader(client: Redis):
    event = await get_event(client)
    print(event)
    fixture = await find_fixture(event.home_team_name, event.away_team_name)
    print(fixture)
    print(fixture.__dict__)

    # event = BetcityMatch(**json.loads(json_data))
    # while True:
    #     json_data = await client.brpop([queue])
    #     msg = await client.rpop(queue)
    #     event = BetcityMatch(**json.loads(json_data))


async def get_event(client: Redis) -> BetcityEvent | None:
    queue = "betcity"
    data = await client.brpop([queue])
    if not data:
        return None

    event = BetcityEvent(**json.loads(data[1]))
    return event


async def find_fixture(home_team: str, away_team: str) -> Fixture:
    sql = Template(
        """
    select * from fixture where home_team_name ilike '%$home_team%'
    and away_team_name ilike '%$away_team%'
    and date > NOW()
    """
    ).substitute({"home_team": home_team, "away_team": away_team})

    fixtures = await Fixture.raw(sql)

    if len(fixtures) > 1:
        return fixtures[0]


async def async_main():
    await init_db()
    client = await redis_connect(RedisDB.BETCITY)

    await reader(client)
    await client.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    run = loop.run_until_complete(async_main())
