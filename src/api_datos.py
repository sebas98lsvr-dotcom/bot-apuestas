import requests, os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Carga .env desde raíz
ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

def obtener_partidos():
    try:
        hoy = datetime.now()

        for i in range(2):  # hoy + mañana
            fecha = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")
            print(f"📅 Buscando partidos: {fecha}")

            params = {"date": fecha}
            r = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params=params, timeout=20)

            if r.status_code != 200:
                print("❌ Error fixtures:", r.status_code)
                continue

            data = r.json()
            partidos = data.get("response", [])

            if partidos:
                print(f"✅ Encontrados: {len(partidos)}")
                return partidos

        print("⚠️ Sin partidos hoy/mañana")
        return []

    except Exception as e:
        print("💥 Error obtener_partidos:", e)
        return []