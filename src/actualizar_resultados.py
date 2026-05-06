import requests, csv, os
from dotenv import load_dotenv

# ======================
# ENV
# ======================
ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
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
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.get(url, params={
            "chat_id": CHAT_ID,
            "text": mensaje
        })
    except:
        pass

# ======================
# CSV
# ======================
ruta = os.path.join(os.path.dirname(__file__), "..", "picks.csv")

if not os.path.exists(ruta):
    print("No hay picks")
    exit()

picks = []

with open(ruta, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        picks.append(row)

# ======================
# PROCESO
# ======================
for p in picks:

    # solo pendientes
    if p.get("resultado") != "pendiente":
        continue

    fixture_id = p.get("fixture_id")

    if not fixture_id:
        continue

    url = f"{BASE_URL}/fixtures"
    params = {"id": fixture_id}

    try:
        r = requests.get(url, headers=HEADERS, params=params)

        if r.status_code != 200:
            continue

        data = r.json().get("response")

        if not data:
            continue

        partido = data[0]
        status = partido["fixture"]["status"]["short"]

        # solo partidos terminados
        if status != "FT":
            continue

        goles_local = partido["goals"]["home"]
        goles_visitante = partido["goals"]["away"]
        total = goles_local + goles_visitante

        resultado = "loss"

        mercado = p.get("mercado", "")

        # ======================
        # LOGICA MERCADOS
        # ======================
        if mercado == "Over 2.5" and total > 2:
            resultado = "win"

        elif mercado == "BTTS" and goles_local > 0 and goles_visitante > 0:
            resultado = "win"

        elif "Corners" in mercado:
            # ⚠️ no tenemos corners reales → lo dejamos como loss por ahora
            resultado = "loss"

        odd = float(p.get("odd", 0))
        stake = float(p.get("stake", 1))

        # ======================
        # PROFIT REAL
        # ======================
        if resultado == "win":
            profit = (odd - 1) * stake
        else:
            profit = -stake

        p["resultado"] = resultado
        p["profit"] = round(profit, 2)

        # ======================
        # TELEGRAM RESULTADO
        # ======================
        emoji = "🟢 WIN" if resultado == "win" else "🔴 LOSS"

        mensaje = (
            f"{emoji}\n\n"
            f"⚽ {p.get('partido')}\n"
            f"🏆 {p.get('liga')}\n"
            f"👉 {p.get('mercado')}\n"
            f"💰 Odd: {odd}\n"
            f"💵 Stake: {stake}\n"
            f"📊 Profit: {p['profit']}"
        )

        enviar_telegram(mensaje)

    except Exception as e:
        print("Error:", e)

# ======================
# GUARDAR
# ======================
with open(ruta, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=picks[0].keys())
    writer.writeheader()
    writer.writerows(picks)

print("✅ Resultados actualizados")