import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# =========================
# CARGAR VARIABLES
# =========================

ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# =========================
# LIGAS / PALABRAS A IGNORAR
# =========================

LIGAS_BLOQUEADAS = [
    "U21",
    "U20",
    "U19",
    "U18",
    "Women",
    "Fem",
    "Reserve",
    "Reserves",
    "Youth",
    "Juvenil",
    "Friendly"
]

# =========================
# VERIFICAR SI LIGA ES VÁLIDA
# =========================

def liga_valida(nombre_liga):
    nombre_liga = nombre_liga.lower()

    for palabra in LIGAS_BLOQUEADAS:
        if palabra.lower() in nombre_liga:
            return False

    return True

# =========================
# OBTENER PARTIDOS
# =========================

def obtener_partidos():

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    partidos = []

    for fecha in [fecha_hoy, fecha_manana]:

        print(f"\n📅 Buscando partidos: {fecha}")

        url = f"{BASE_URL}/fixtures?date={fecha}"

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            print("🌐 STATUS:", response.status_code)

            # =========================
            # ERROR API
            # =========================

            if response.status_code == 403:
                print("❌ API bloqueada o KEY inválida")
                continue

            if response.status_code != 200:
                print(f"❌ Error API: {response.status_code}")
                continue

            data = response.json()

            if "response" not in data:
                print("❌ Respuesta inválida")
                continue

            fixtures = data["response"]

            print(f"⚽ Partidos encontrados: {len(fixtures)}")

            # =========================
            # FILTRAR PARTIDOS
            # =========================

            for partido in fixtures:

                try:

                    liga = partido["league"]["name"]

                    if not liga_valida(liga):
                        continue

                    # Validar datos mínimos
                    if (
                        "teams" not in partido
                        or "fixture" not in partido
                    ):
                        continue

                    partidos.append(partido)

                except Exception:
                    continue

        except requests.exceptions.Timeout:
            print("⏰ Timeout API")

        except Exception as e:
            print("❌ ERROR GENERAL:", e)

    # =========================
    # ORDENAR POR FECHA
    # =========================

    partidos.sort(
        key=lambda x: x["fixture"]["date"]
    )

    print(f"\n✅ TOTAL PARTIDOS VÁLIDOS: {len(partidos)}")

    return partidos