import requests
import csv
import os
import shutil
from datetime import datetime
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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# ======================
# TELEGRAM
# ======================

def enviar_telegram(mensaje):

    try:

        if not TELEGRAM_TOKEN or not CHAT_ID:
            print("⚠️ Telegram no configurado")
            return False

        url = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_TOKEN}/sendMessage"
        )

        r = requests.get(
            url,
            params={
                "chat_id": CHAT_ID,
                "text": mensaje
            },
            timeout=20
        )

        if r.status_code == 200:
            print("✅ Telegram enviado")
            return True

        print("⚠️ Telegram status:", r.status_code)
        return False

    except Exception as e:

        print("❌ Error Telegram:", e)
        return False

# ======================
# RUTAS
# ======================

ruta = os.path.join(
    BASE_DIR,
    "picks.csv"
)

ruta_backup_dir = os.path.join(
    BASE_DIR,
    "backups"
)

os.makedirs(
    ruta_backup_dir,
    exist_ok=True
)

# ======================
# VALIDACIONES
# ======================

if not API_KEY:

    print("❌ No se encontró API_FOOTBALL_KEY en .env")
    exit()

if not os.path.exists(ruta):

    print("⚠️ No existe picks.csv")
    exit()

if os.path.getsize(ruta) == 0:

    print("⚠️ picks.csv está vacío. No se modifica.")
    exit()

# ======================
# HELPERS
# ======================

def limpiar_texto(valor):

    if valor is None:
        return ""

    return str(valor).strip()


def to_float(valor, default=0.0):

    try:

        if valor is None:
            return default

        valor = str(valor).strip()

        if valor == "":
            return default

        return float(valor)

    except:

        return default


def evaluar_pick(mercado, goles_local, goles_visitante):

    mercado = limpiar_texto(
        mercado
    ).lower()

    total = goles_local + goles_visitante

    if mercado == "over 1.5":

        return "win" if total > 1 else "loss"

    if mercado == "over 2.5":

        return "win" if total > 2 else "loss"

    if mercado == "over 3.5":

        return "win" if total > 3 else "loss"

    if mercado == "btts":

        return (
            "win"
            if goles_local > 0 and goles_visitante > 0
            else "loss"
        )

    return "pendiente"


def crear_mensaje_resultado(p, resultado, goles_local, goles_visitante, odd, stake, profit):

    emoji = (
        "🟢 WIN"
        if resultado == "win"
        else "🔴 LOSS"
    )

    return (
        f"{emoji}\n\n"
        f"⚽ {p.get('partido')}\n"
        f"🏆 {p.get('liga')}\n"
        f"👉 {p.get('mercado')}\n"
        f"📊 Marcador: {goles_local}-{goles_visitante}\n"
        f"💰 Odd: {odd}\n"
        f"💵 Stake: {stake}\n"
        f"📈 Profit: {round(profit, 2)}"
    )


# ======================
# LEER CSV
# ======================

picks = []

with open(
    ruta,
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    if not reader.fieldnames:

        print("⚠️ picks.csv no tiene encabezados. No se modifica.")
        exit()

    columnas_originales = list(reader.fieldnames)

    for row in reader:

        # Ignorar filas completamente vacías
        if not any(
            str(v).strip()
            for v in row.values()
            if v is not None
        ):
            continue

        if "notificado" not in row:
            row["notificado"] = "no"

        if "score" not in row:
            row["score"] = ""

        if "profit" not in row:
            row["profit"] = "0"

        if "resultado" not in row:
            row["resultado"] = "pendiente"

        picks.append(row)

# ======================
# VALIDAR PICKS
# ======================

if len(picks) == 0:

    print("⚠️ No hay picks. No se sobrescribe picks.csv.")
    exit()

# ======================
# PROCESO
# ======================

wins_actualizadas = 0
losses_actualizadas = 0
profit_actualizado = 0.0

hubo_actualizaciones = False

for p in picks:

    resultado_actual = limpiar_texto(
        p.get("resultado", "")
    ).lower()

    # IMPORTANTE:
    # Revisar TODAS las pendientes,
    # aunque notificado sea "si".
    if resultado_actual != "pendiente":
        continue

    fixture_id = limpiar_texto(
        p.get("fixture_id", "")
    )

    if not fixture_id:

        print("⚠️ Pick sin fixture_id:", p.get("partido"))
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

            print(
                f"⚠️ API status {r.status_code} para fixture {fixture_id}"
            )
            continue

        json_data = r.json()

        data = json_data.get(
            "response",
            []
        )

        if not data:

            print(
                f"⚠️ Sin respuesta API para fixture {fixture_id}"
            )
            continue

        partido_api = data[0]

        status = partido_api["fixture"]["status"]["short"]

        print(
            f"📡 {p.get('partido')} | Status API: {status}"
        )

        # Solo partidos finalizados reales
        if status not in [
            "FT",
            "AET",
            "PEN"
        ]:
            continue

        goles_local = partido_api["goals"]["home"]
        goles_visitante = partido_api["goals"]["away"]

        if goles_local is None or goles_visitante is None:

            print(
                "⚠️ Partido finalizado pero sin goles:",
                p.get("partido")
            )
            continue

        goles_local = int(goles_local)
        goles_visitante = int(goles_visitante)

        resultado = evaluar_pick(
            p.get("mercado", ""),
            goles_local,
            goles_visitante
        )

        if resultado == "pendiente":

            print(
                "⚠️ Mercado no reconocido:",
                p.get("mercado"),
                "|",
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

            wins_actualizadas += 1

        else:

            profit = round(
                -stake,
                2
            )

            losses_actualizadas += 1

        profit_actualizado += profit

        # Guardar resultado
        p["score"] = f"{goles_local}-{goles_visitante}"
        p["resultado"] = resultado
        p["profit"] = str(profit)

        # Telegram solo si NO se había notificado antes
        notificado_actual = limpiar_texto(
            p.get("notificado", "")
        ).lower()

        if notificado_actual != "si":

            mensaje = crear_mensaje_resultado(
                p,
                resultado,
                goles_local,
                goles_visitante,
                odd,
                stake,
                profit
            )

            enviado = enviar_telegram(
                mensaje
            )

            if enviado:
                p["notificado"] = "si"

        else:

            # Si ya estaba notificado como pick,
            # no repetimos Telegram de resultado.
            # Pero sí dejamos la fila actualizada.
            p["notificado"] = "si"

        hubo_actualizaciones = True

        print(
            f"✅ Actualizado: {p.get('partido')} "
            f"{p.get('mercado')} "
            f"{goles_local}-{goles_visitante} "
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
# SI NO HUBO CAMBIOS
# ======================

if not hubo_actualizaciones:

    print("ℹ️ No hubo partidos finalizados para actualizar.")
    print("✅ picks.csv no fue modificado.")
    exit()

# ======================
# BACKUP ANTES DE GUARDAR
# ======================

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

ruta_backup = os.path.join(
    ruta_backup_dir,
    f"picks_backup_{timestamp}.csv"
)

shutil.copy2(
    ruta,
    ruta_backup
)

print(
    f"🛡️ Backup creado: {ruta_backup}"
)

# ======================
# GUARDAR CSV SEGURO
# ======================

campos_base = [
    "fecha",
    "fixture_id",
    "partido",
    "liga",
    "mercado",
    "odd",
    "prob",
    "value",
    "score",
    "stake",
    "resultado",
    "profit",
    "notificado"
]

campos = []

for c in columnas_originales:

    if c not in campos:
        campos.append(c)

for c in campos_base:

    if c not in campos:
        campos.append(c)

for p in picks:

    for key in p.keys():

        if key not in campos:
            campos.append(key)

ruta_temp = ruta + ".tmp"

with open(
    ruta_temp,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=campos,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(picks)

os.replace(
    ruta_temp,
    ruta
)

# ======================
# RESUMEN FINAL
# ======================

total_actualizadas = wins_actualizadas + losses_actualizadas

if total_actualizadas > 0:

    winrate = round(
        (wins_actualizadas / total_actualizadas) * 100,
        2
    )

    resumen = (
        "📊 RESUMEN RESULTADOS ACTUALIZADOS\n\n"
        f"🎯 Picks actualizadas: {total_actualizadas}\n"
        f"🟢 Ganadas: {wins_actualizadas}\n"
        f"🔴 Perdidas: {losses_actualizadas}\n\n"
        f"💰 Profit actualizado: {round(profit_actualizado, 2)}\n"
        f"📈 Winrate actualizado: {winrate}%"
    )

    enviar_telegram(
        resumen
    )

print("✅ Resultados actualizados")