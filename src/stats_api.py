import requests, os
from dotenv import load_dotenv

ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

def obtener_stats_equipo(team_id, league_id, season):
    try:
        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }

        r = requests.get(f"{BASE_URL}/teams/statistics", headers=HEADERS, params=params, timeout=20)

        if r.status_code != 200:
            return None

        return r.json().get("response", {})

    except:
        return None