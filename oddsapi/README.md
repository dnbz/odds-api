# Odds API
There are 3 parts to this project:
- Telegram bot that responds to messages
- Queue worker that publishes messages to a telegram channel and refreshes data from football-api periodically
- Database writer that reads redis queues from parsers and writes data to the database

## Bot
Bot is written using the pyrogram library

## Queue
Queue worker is [arq](https://github.com/samuelcolvin/arq)

Sends messages to a telegram channel with new events with matching criteria

Also imports new events/odds from [football-api](https://rapidapi.com/api-sports/api/API-FOOTBALL)

## Database writer
Receives data about new events from redis queue(`lpush` + `rpop`)

Matches with the events from [football-api](https://rapidapi.com/api-sports/api/API-FOOTBALL)

Checks for duplicates and writes data in correct format


# Setup
This project is deployed using `docker-compose`

Fill in/copy `./.env` and `./.env.prod` with correct values prior to running the project.
All the relevant fields are described in `settings.py` 