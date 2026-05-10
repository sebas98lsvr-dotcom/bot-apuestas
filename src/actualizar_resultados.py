import requests
import csv
import os
from dotenv import load_dotenv

# ======================
# ENV
# ======================

ruta_env = os.path.join(
    os.path.dirname(__file__),
    "..",
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

        url = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_TOKEN}/sendMessage"
        )

        requests.get(
            url,
            params={
                "chat_id": CHAT_ID,
                "text": mensaje
            },
            timeout=20
        )

        print("✅ Telegram enviado")

    except Exception as e:

        print("❌ Error Telegram:", e)

# ======================
# CSV
# ======================

ruta = os.path.join(
    os.path.dirname(__file__),
    "..",
    "picks.csv"
)

if not os.path.exists(ruta):

    print("⚠️ No existe picks.csv")
    exit()

picks = []

with open(
    ruta,
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        # proteger CSV viejos
        if "notificado" not in row:
            row["notificado"] = "no"

        picks.append(row)

# ======================
# VALIDAR PICKS
# ======================

if len(picks) == 0:

    print("⚠️ No hay picks")
    exit()

# ======================
# ESTADISTICAS
# ======================

wins = 0
losses = 0
profit_total = 0

hubo_actualizaciones = False

# ======================
# PROCESO
# ======================

for p in picks:

    # solo pendientes NO notificados
    if (
        p.get("resultado") != "pendiente"
        or p.get("notificado") == "si"
    ):
        continue

    fixture_id = p.get("fixture_id")

    if not fixture_id:
        continue

    url = f"{BASE_URL}/fixtures"

    params = {
        "id": fixture_id
    }

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            continue

        data = r.json().get("response")

        if not data:
            continue

        partido = data[0]

        status = partido["fixture"]["status"]["short"]

        print(f"📡 Status API: {status}")

        # solo terminados reales
        if status not in ["FT", "AET", "PEN"]:
            continue

        goles_local = partido["goals"]["home"]
        goles_visitante = partido["goals"]["away"]

        # seguridad extra
        if goles_local is None or goles_visitante is None:
            continue

        total = goles_local + goles_visitante

        # ======================
        # PRINT RESULTADO
        # ======================

        print(
            f"{p.get('partido')} "
            f"{status} "
            f"{goles_local}-{goles_visitante}"
        )

        resultado = "loss"

        mercado = p.get("mercado", "")

        # ======================
        # LOGICA MERCADOS
        # ======================

        # OVER 1.5
        if (
            mercado == "Over 1.5"
            and total > 1
        ):

            resultado = "win"

        # OVER 2.5
        elif (
            mercado == "Over 2.5"
            and total > 2
        ):

            resultado = "win"

        # BTTS
        elif (
            mercado == "BTTS"
            and goles_local > 0
            and goles_visitante > 0
        ):

            resultado = "win"

        odd = float(
            p.get("odd", 0)
        )

        stake = float(
            p.get("stake", 1)
        )

        # ======================
        # PROFIT
        # ======================

        if resultado == "win":

            profit = (
                (odd - 1) * stake
            )

            wins += 1

        else:

            profit = -stake

            losses += 1

        profit_total += profit

        p["resultado"] = resultado

        p["profit"] = round(
            profit,
            2
        )

        # evitar repetir telegram
        p["notificado"] = "si"

        hubo_actualizaciones = True

        # ======================
        # TELEGRAM INDIVIDUAL
        # ======================

        emoji = (
            "🟢 WIN"
            if resultado == "win"
            else "🔴 LOSS"
        )

        mensaje = (
            f"{emoji}\n\n"
            f"⚽ {p.get('partido')}\n"
            f"🏆 {p.get('liga')}\n"
            f"👉 {p.get('mercado')}\n"
            f"📊 Marcador: {goles_local}-{goles_visitante}\n"
            f"💰 Odd: {odd}\n"
            f"💵 Stake: {stake}\n"
            f"📈 Profit: {round(profit,2)}"
        )

        enviar_telegram(
            mensaje
        )

    except Exception as e:

        print("❌ Error:", e)

# ======================
# GUARDAR CSV
# ======================

campos = [
    "fecha",
    "fixture_id",
    "partido",
    "liga",
    "mercado",
    "odd",
    "prob",
    "value",
    "stake",
    "resultado",
    "profit",
    "notificado"
]

with open(
    ruta,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=campos
    )

    writer.writeheader()

    writer.writerows(picks)

# ======================
# RESUMEN FINAL
# ======================

total_picks = wins + losses

if (
    total_picks > 0
    and hubo_actualizaciones
):

    winrate = round(
        (wins / total_picks) * 100,
        2
    )

    resumen = (
        "📊 RESUMEN DEL DÍA\n\n"
        f"🎯 Total Picks: {total_picks}\n"
        f"🟢 Ganadas: {wins}\n"
        f"🔴 Perdidas: {losses}\n\n"
        f"💰 Profit Total: {round(profit_total,2)}\n"
        f"📈 Winrate: {winrate}%"
    )

    enviar_telegram(
        resumen
    )

print("✅ Resultados actualizados")