import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"


def obtener_partidos():
    url = f"{BASE_URL}/fixtures"

    # 🔥 CAMBIA LA FECHA SI NO HAY PARTIDOS
    params = {
        "date": "2026-05-04"
    }

    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json()

    return data.get("response", [])


def obtener_ultimos_partidos(team_id):
    url = f"{BASE_URL}/fixtures"

    params = {
        "team": team_id,
        "last": 5
    }

    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json()

    return data.get("response", [])