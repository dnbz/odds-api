#!/usr/bin/env python3
import requests
from requests import Response
from oddsapi.settings import API_HOST, API_KEY

def get_api(path: str) -> Response:
    url = f"https://{API_HOST}/{path}"

    headers = {
        'x-rapidapi-host': API_HOST,
        'x-rapidapi-key': API_KEY
    }

    return requests.get(url, headers=headers)

# odds = get_api('odds?')
