#!/bin/sh

echo 'Running migrations'
pdm run aerich upgrade

echo 'Running worker'
pdm run worker