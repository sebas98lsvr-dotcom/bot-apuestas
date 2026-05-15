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
            print(
                f"⚠️ Error stats equipo "
                f"| Team: {team_id} "
                f"| League: {league_id} "
                f"| Season: {season} "
                f"| Status: {r.status_code}"
            )
            return None

        return r.json().get("response", {})

    except Exception as e:

        print("❌ Error obtener_stats_equipo:", e)
        return None

# ==============================
# FORMA RECIENTE FILTRADA
# ==============================

def obtener_forma_reciente(team_id, league_id, season, venue=None):

    try:

        params = {
            "team": team_id,
            "league": league_id,
            "season": season,
            "last": 10
        }

        r = requests.get(
            f"{BASE_URL}/fixtures",
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            print(
                f"⚠️ Error forma reciente "
                f"| Team: {team_id} "
                f"| League: {league_id} "
                f"| Season: {season} "
                f"| Status: {r.status_code}"
            )
            return None

        data = r.json().get("response", [])

        if not data:
            print(
                f"⚠️ Sin partidos recientes "
                f"| Team: {team_id} "
                f"| League: {league_id} "
                f"| Season: {season}"
            )
            return None

        goles_favor = 0
        goles_contra = 0
        partidos = 0

        for p in data:

            status = p.get("fixture", {}).get("status", {}).get("short")

            if status != "FT":
                continue

            home_id = p.get("teams", {}).get("home", {}).get("id")
            away_id = p.get("teams", {}).get("away", {}).get("id")

            goles_home = p.get("goals", {}).get("home")
            goles_away = p.get("goals", {}).get("away")

            if goles_home is None or goles_away is None:
                continue

            es_local = team_id == home_id
            es_visitante = team_id == away_id

            if venue == "home" and not es_local:
                continue

            if venue == "away" and not es_visitante:
                continue

            if es_local:

                goles_favor += goles_home
                goles_contra += goles_away

            elif es_visitante:

                goles_favor += goles_away
                goles_contra += goles_home

            else:
                continue

            partidos += 1

        if partidos < 3:
            print(
                f"⚠️ Forma reciente insuficiente "
                f"| Team: {team_id} "
                f"| Venue: {venue} "
                f"| Partidos válidos: {partidos}"
            )
            return None

        return {
            "gf": goles_favor / partidos,
            "gc": goles_contra / partidos,
            "partidos": partidos
        }

    except Exception as e:

        print("❌ Error obtener_forma_reciente:", e)
        return None