#!/bin/sh


mkdir -p /app/logs

# run database migrations
pdm run migrate

# import initial data if not already imported
pdm run autoimport

exec supervisord
