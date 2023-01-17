#!/bin/sh

echo 'Running migrations'
pdm run aerich upgrade

echo 'Running parser listener'
pdm run parser-listener