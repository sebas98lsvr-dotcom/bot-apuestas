import os
import csv
import shutil
import requests
from datetime import datetime
from dotenv import load_dotenv

# ======================
# RUTAS
# ======================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

PICKS_FILE = os.path.join(
    BASE_DIR,
    "picks.csv"
)

BACKUP_DIR = os.path.join(
    BASE_DIR,
    "backups"
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

os.makedirs(
    BACKUP_DIR,
    exist_ok=True
)

# ======================
# ENV
# ======================

load_dotenv(ENV_FILE)

API_KEY = os.getenv("API_FOOTBALL_KEY")

if not API_KEY:
    print("❌ No se encontró API_FOOTBALL_KEY")
    exit()

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# ======================
# VALIDAR
# ======================

if not os.path.exists(PICKS_FILE):
    print("❌ No existe picks.csv")
    exit()

# ======================
# BACKUP
# ======================

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_file = os.path.join(
    BACKUP_DIR,
    f"picks_forzar_ft_backup_{timestamp}.csv"
)

shutil.copy2(
    PICKS_FILE,
    backup_file
)

print(f"🛡️ Backup creado: {backup_file}")

# ======================
# LEER CSV
# ======================

with open(
    PICKS_FILE,
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    fieldnames = reader.fieldnames

    if not fieldnames:
        print("❌ CSV sin encabezados")
        exit()

    picks = list(reader)

if not picks:
    print("⚠️ No hay picks")
    exit()

# asegurar columnas
for col in [
    "score",
    "resultado",
    "profit",
    "notificado"
]:
    if col not in fieldnames:
        fieldnames.append(col)

actualizados = 0

# ======================
# HELPERS
# ======================

def to_float(x, default=0.0):
    try:
        if x is None:
            return default
        x = str(x).strip()
        if x == "":
            return default
        return float(x)
    except:
        return default


def evaluar_pick(mercado, goles_local, goles_visitante):

    total = goles_local + goles_visitante

    mercado = str(
        mercado
    ).strip().lower()

    if mercado == "over 1.5":
        return "win" if total > 1 else "loss"

    if mercado == "over 2.5":
        return "win" if total > 2 else "loss"

    if mercado == "btts":
        return "win" if goles_local > 0 and goles_visitante > 0 else "loss"

    # Si no reconoce mercado, dejar pendiente
    return "pendiente"


# ======================
# PROCESAR
# ======================

for p in picks:

    resultado_actual = str(
        p.get("resultado", "")
    ).strip().lower()

    if resultado_actual != "pendiente":
        continue

    fixture_id = str(
        p.get("fixture_id", "")
    ).strip()

    if not fixture_id:
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
            print("⚠️ API error", r.status_code, p.get("partido"))
            continue

        data = r.json().get(
            "response",
            []
        )

        if not data:
            print("⚠️ Sin data:", p.get("partido"))
            continue

        partido = data[0]

        status = partido["fixture"]["status"]["short"]

        print(
            f"📡 {p.get('partido')} | Status: {status}"
        )

        if status not in [
            "FT",
            "AET",
            "PEN"
        ]:
            continue

        goles_local = partido["goals"]["home"]
        goles_visitante = partido["goals"]["away"]

        if goles_local is None or goles_visitante is None:
            continue

        resultado = evaluar_pick(
            p.get("mercado", ""),
            int(goles_local),
            int(goles_visitante)
        )

        if resultado == "pendiente":
            print(
                "⚠️ Mercado no reconocido:",
                p.get("mercado"),
                p.get("partido")
            )
            continue

        odd = to_float(
            p.get("odd", 0),
            0
        )

        stake = to_float(
            p.get("stake", 30),
            30
        )

        if resultado == "win":

            profit = round(
                (odd - 1) * stake,
                2
            )

        else:

            profit = round(
                -stake,
                2
            )

        p["score"] = f"{goles_local}-{goles_visitante}"
        p["resultado"] = resultado
        p["profit"] = str(profit)
        p["notificado"] = "si"

        actualizados += 1

        print(
            f"✅ Actualizado: {p.get('partido')} "
            f"{p.get('mercado')} "
            f"{p['score']} "
            f"{resultado} "
            f"{profit}"
        )

    except Exception as e:

        print(
            "❌ Error:",
            p.get("partido"),
            e
        )

# ======================
# GUARDAR
# ======================

if actualizados == 0:

    print("ℹ️ No se actualizó ningún pendiente")
    exit()

temp_file = PICKS_FILE + ".tmp"

with open(
    temp_file,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(picks)

os.replace(
    temp_file,
    PICKS_FILE
)

print(f"✅ Pendientes actualizados: {actualizados}")