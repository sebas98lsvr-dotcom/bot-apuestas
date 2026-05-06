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


def obtener_stats(team_id, league_id, season):
    try:
        url = f"{BASE_URL}/teams/statistics"

        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }

        r = requests.get(url, headers=HEADERS, params=params, timeout=20)

        if r.status_code != 200:
            return None

        data = r.json().get("response")

        # Manejo robusto (lista o dict)
        if isinstance(data, list):
            if not data:
                return None
            data = data[0]

        if not isinstance(data, dict):
            return None

        goles_for = float(data["goals"]["for"]["average"]["total"])
        goles_against = float(data["goals"]["against"]["average"]["total"])

        return goles_for, goles_against

    except Exception as e:
        print("💥 Error stats:", e)
        return None


def calcular_corners_esperados(home_id, away_id, league_id, season):
    home = obtener_stats(home_id, league_id, season)
    away = obtener_stats(away_id, league_id, season)

    # Fallback seguro (NUNCA None)
    if home is None or away is None:
        return 9.0

    hf, ha = home
    af, aa = away

    # Modelo derivado (estable)
    corners = ((hf + af) * 2.8 + (ha + aa) * 1.5) / 2

    return round(max(5, min(corners, 14)), 2)