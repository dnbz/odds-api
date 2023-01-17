#!/bin/sh

echo 'Running migrations'
pdm run aerich upgrade

echo 'Running telegram bot'
pdm run tg-bot