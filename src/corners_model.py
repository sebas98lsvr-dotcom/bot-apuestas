import requests
import os
from dotenv import load_dotenv

# =========================
# CARGAR ENV
# =========================

ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# =========================
# OBTENER STATS EQUIPO
# =========================

def obtener_stats(team_id, league_id, season):

    try:

        url = f"{BASE_URL}/teams/statistics"

        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }

        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            return None

        data = r.json().get("response")

        if not isinstance(data, dict):
            return None

        goles_for = float(
            data["goals"]["for"]["average"]["total"]
        )

        goles_against = float(
            data["goals"]["against"]["average"]["total"]
        )

        partidos = int(
            data["fixtures"]["played"]["total"]
        )

        return {
            "gf": goles_for,
            "ga": goles_against,
            "pj": partidos
        }

    except Exception as e:
        print("💥 Error stats:", e)
        return None

# =========================
# MODELO CONSERVADOR CORNERS
# =========================

def calcular_corners_esperados(
    home_id,
    away_id,
    league_id,
    season
):

    home = obtener_stats(
        home_id,
        league_id,
        season
    )

    away = obtener_stats(
        away_id,
        league_id,
        season
    )

    # fallback seguro
    if home is None or away is None:
        return 9.0

    # evitar muestras pequeñas
    if home["pj"] < 5 or away["pj"] < 5:
        return 9.0

    # =========================
    # FACTORES OFENSIVOS
    # =========================

    ataque = (
        home["gf"] +
        away["gf"]
    ) / 2

    defensa = (
        home["ga"] +
        away["ga"]
    ) / 2

    # =========================
    # MODELO MÁS CONSERVADOR
    # =========================

    corners = (
        7.5 +
        (ataque * 0.8) +
        (defensa * 0.5)
    )

    # limitar extremos
    corners = max(7, min(corners, 12))

    return round(corners, 2)