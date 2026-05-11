import requests
import os
from dotenv import load_dotenv

ruta_env = os.path.join(
    os.path.dirname(__file__),
    "..",
    ".env"
)

load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# ==============================
# STATS TEMPORADA
# ==============================

def obtener_stats_equipo(team_id, league_id, season):

    try:

        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }

        r = requests.get(
            f"{BASE_URL}/teams/statistics",
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            return None

        return r.json().get("response", {})

    except:
        return None

# ==============================
# FORMA RECIENTE
# ==============================

def obtener_forma_reciente(team_id):

    try:

        params = {
            "team": team_id,
            "last": 5
        }

        r = requests.get(
            f"{BASE_URL}/fixtures",
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            return None

        data = r.json().get("response", [])

        if not data:
            return None

        goles_favor = 0
        goles_contra = 0
        partidos = 0

        for p in data:

            home_id = p["teams"]["home"]["id"]
            away_id = p["teams"]["away"]["id"]

            goles_home = p["goals"]["home"]
            goles_away = p["goals"]["away"]

            if goles_home is None or goles_away is None:
                continue

            if team_id == home_id:

                goles_favor += goles_home
                goles_contra += goles_away

            else:

                goles_favor += goles_away
                goles_contra += goles_home

            partidos += 1

        if partidos == 0:
            return None

        return {

            "gf": goles_favor / partidos,
            "gc": goles_contra / partidos
        }

    except:
        return None