import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Intentar cargar .env localmente
ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

# Obtener API KEY
API_KEY = os.getenv("API_FOOTBALL_KEY")

# DEBUG
print("===================================")
print("🔑 API KEY:", API_KEY)
print("===================================")

# Headers correctos
HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

def obtener_partidos():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    partidos = []

    for fecha in [fecha_hoy, fecha_manana]:
        print(f"📅 Buscando partidos: {fecha}")

        url = f"{BASE_URL}/fixtures?date={fecha}"

        try:
            response = requests.get(url, headers=HEADERS)

            print("🌐 STATUS CODE:", response.status_code)

            if response.status_code == 403:
                print("❌ ERROR 403 → API bloqueada o KEY inválida")
                print("HEADERS:", HEADERS)
                continue

            if response.status_code != 200:
                print(f"❌ Error fixtures: {response.status_code}")
                continue

            data = response.json()

            if "response" not in data:
                print("❌ Respuesta inválida")
                continue

            partidos.extend(data["response"])

        except Exception as e:
            print("❌ ERROR GENERAL:", e)

    return partidos