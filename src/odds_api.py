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


def obtener_odds(fixture_id):
    try:
        url = f"{BASE_URL}/odds"

        params = {
            "fixture": fixture_id
        }

        r = requests.get(url, headers=HEADERS, params=params, timeout=20)

        if r.status_code != 200:
            return []

        # 🔥 IMPORTANTE
        return r.json().get("response", [])

    except Exception as e:
        print("💥 Error odds:", e)
        return []