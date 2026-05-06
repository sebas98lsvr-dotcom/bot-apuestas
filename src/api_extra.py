import requests
import os
from dotenv import load_dotenv

ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"


def obtener_corners_partido(fixture_id):
    try:
        url = f"{BASE_URL}/fixtures/statistics"

        params = {
            "fixture": fixture_id
        }

        r = requests.get(url, headers=HEADERS, params=params)

        if r.status_code != 200:
            return None

        data = r.json().get("response", [])

        if not data:
            return None

        corners = {}

        for team in data:
            for stat in team["statistics"]:
                if stat["type"] == "Corner Kicks":
                    corners[team["team"]["name"]] = stat["value"]

        return corners

    except Exception as e:
        print("💥 Error corners real:", e)
        return None