#!/bin/sh


mkdir -p /app/logs

# run database migrations
alembic upgrade head

# import initial data if not already imported
pdm run autoimport

exec supervisord
