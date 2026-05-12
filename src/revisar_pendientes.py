import os
import csv
import requests
from dotenv import load_dotenv

# ======================
# ENV
# ======================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

ruta_env = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

PICKS_FILE = os.path.join(
    BASE_DIR,
    "picks.csv"
)

# ======================
# VALIDAR
# ======================

if not os.path.exists(PICKS_FILE):
    print("❌ No existe picks.csv")
    exit()

# ======================
# LEER PENDIENTES
# ======================

with open(
    PICKS_FILE,
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    pendientes = [
        row for row in reader
        if str(row.get("resultado", "")).strip().lower() == "pendiente"
    ]

print("🔎 Pendientes encontrados:", len(pendientes))
print("=" * 60)

# ======================
# CONSULTAR API
# ======================

for p in pendientes:

    fixture_id = str(
        p.get("fixture_id", "")
    ).strip()

    if not fixture_id:
        print("⚠️ Sin fixture_id:", p.get("partido"))
        continue

    try:

        r = requests.get(
            f"{BASE_URL}/fixtures",
            headers=HEADERS,
            params={
                "id": fixture_id
            },
            timeout=20
        )

        if r.status_code != 200:
            print("❌ API ERROR", r.status_code, p.get("partido"))
            continue

        data = r.json().get("response", [])

        if not data:
            print("⚠️ Sin data API:", fixture_id, p.get("partido"))
            continue

        partido_api = data[0]

        status_short = partido_api["fixture"]["status"]["short"]
        status_long = partido_api["fixture"]["status"]["long"]
        elapsed = partido_api["fixture"]["status"].get("elapsed")

        home = partido_api["teams"]["home"]["name"]
        away = partido_api["teams"]["away"]["name"]

        goles_home = partido_api["goals"]["home"]
        goles_away = partido_api["goals"]["away"]

        fecha_api = partido_api["fixture"]["date"]

        print(f"⚽ CSV: {p.get('partido')}")
        print(f"🆔 Fixture ID: {fixture_id}")
        print(f"📅 API Fecha: {fecha_api}")
        print(f"🏟️ API Partido: {home} vs {away}")
        print(f"📡 Status: {status_short} - {status_long} - Min: {elapsed}")
        print(f"🥅 Goles API: {goles_home}-{goles_away}")
        print("-" * 60)

    except Exception as e:

        print("❌ Error:", p.get("partido"), e)