import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
    import pytz

# =========================
# CARGAR VARIABLES
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
# ZONA HORARIA COLOMBIA
# =========================

def ahora_colombia():

    if ZoneInfo is not None:
        return datetime.now(
            ZoneInfo("America/Bogota")
        )

    zona = pytz.timezone(
        "America/Bogota"
    )

    return datetime.now(
        zona
    )

# =========================
# CONVERTIR FECHA API A COLOMBIA
# =========================

def fecha_api_a_colombia(fecha_api):

    try:

        fecha_api = str(fecha_api).strip()

        fecha_utc = datetime.fromisoformat(
            fecha_api.replace("Z", "+00:00")
        )

        if fecha_utc.tzinfo is None:

            if ZoneInfo is not None:
                fecha_utc = fecha_utc.replace(
                    tzinfo=ZoneInfo("UTC")
                )
            else:
                fecha_utc = pytz.utc.localize(
                    fecha_utc
                )

        if ZoneInfo is not None:

            return fecha_utc.astimezone(
                ZoneInfo("America/Bogota")
            )

        zona = pytz.timezone(
            "America/Bogota"
        )

        return fecha_utc.astimezone(
            zona
        )

    except Exception:

        return None

# =========================
# LIGAS / PALABRAS A IGNORAR
# =========================

LIGAS_BLOQUEADAS = [

    "U23",
    "U21",
    "U20",
    "U19",
    "U18",
    "U17",
    "U16",
    "U15",

    "Women",
    "Woman",
    "Fem",
    "Femenino",
    "Feminine",
    "W League",

    "Reserve",
    "Reserves",
    "Reservas",
    "Youth",
    "Juvenil",
    "Junior",
    "Academy",
    "Development",
    "Primavera",

    "Friendly",
    "Friendlies",
    "Amistoso",
    "Club Friendlies",

    "Amateur",
    "Regional",
    "County",
    "State League",
    "District"
]

# =========================
# VERIFICAR SI LIGA ES VÁLIDA
# =========================

def liga_valida(nombre_liga):

    try:

        nombre_liga = str(nombre_liga).lower()

        for palabra in LIGAS_BLOQUEADAS:

            if palabra.lower() in nombre_liga:
                return False

        return True

    except Exception:

        return False

# =========================
# OBTENER PARTIDOS
# =========================

def obtener_partidos():

    ahora = ahora_colombia()
    limite = ahora + timedelta(hours=24)

    fecha_hoy = ahora.strftime("%Y-%m-%d")
    fecha_manana = (ahora + timedelta(days=1)).strftime("%Y-%m-%d")

    partidos = []

    for fecha in [fecha_hoy, fecha_manana]:

        print(f"\n📅 Buscando partidos: {fecha}")

        url = f"{BASE_URL}/fixtures"

        params = {
            "date": fecha
        }

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
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

                    liga = partido.get("league", {}).get("name", "")

                    if not liga_valida(liga):
                        continue

                    if (
                        "teams" not in partido
                        or "fixture" not in partido
                    ):
                        continue

                    status = partido.get(
                        "fixture",
                        {}
                    ).get(
                        "status",
                        {}
                    ).get(
                        "short",
                        ""
                    )

                    if status != "NS":
                        continue

                    fecha_api = partido.get(
                        "fixture",
                        {}
                    ).get(
                        "date"
                    )

                    fecha_col = fecha_api_a_colombia(
                        fecha_api
                    )

                    if fecha_col is None:
                        continue

                    if fecha_col < ahora:
                        continue

                    if fecha_col > limite:
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
    print(
        f"🕒 Ventana usada Colombia: "
        f"{ahora.strftime('%Y-%m-%d %H:%M')} "
        f"hasta {limite.strftime('%Y-%m-%d %H:%M')}"
    )

    return partidos