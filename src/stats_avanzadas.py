import requests
import os
from dotenv import load_dotenv

# =========================
# ENV
# =========================

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

# =========================
# OBTENER ESTADISTICAS
# =========================

def obtener_estadisticas_fixture(fixture_id):

    url = f"{BASE_URL}/fixtures/statistics"

    params = {
        "fixture": fixture_id
    }

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            return None

        data = r.json().get("response")

        return data

    except Exception as e:

        print("❌ Error stats avanzadas:", e)

        return None