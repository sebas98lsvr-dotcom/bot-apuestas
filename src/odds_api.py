import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"


def obtener_odds(fixture_id):
    url = f"{BASE_URL}/odds"

    params = {
        "fixture": fixture_id
    }

    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json()

    return data.get("response", [])