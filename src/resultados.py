import csv
import os
import requests
from dotenv import load_dotenv

# =========================
# ENV
# =========================
ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "x-apisports-key": API_KEY
}

# =========================
# TELEGRAM
# =========================
def enviar_telegram(mensaje):

    try:

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        requests.get(url, params={
            "chat_id": CHAT_ID,
            "text": mensaje
        })

        print("✅ Resultado enviado")

    except Exception as e:
        print("Error Telegram:", e)

# =========================
# OBTENER FIXTURE
# =========================
def obtener_fixture(fixture_id):

    url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"

    r = requests.get(url, headers=HEADERS)

    data = r.json()

    if data["response"]:
        return data["response"][0]

    return None

# =========================
# VERIFICAR PICK
# =========================
def verificar_pick(pick, fixture):

    goles_local = fixture["goals"]["home"]
    goles_visitante = fixture["goals"]["away"]

    total_goles = goles_local + goles_visitante

    market = pick["mercado"]

    # ======================
    # OVER 2.5
    # ======================
    if market == "Over 2.5":

        return total_goles > 2

    # ======================
    # BTTS
    # ======================
    if market == "BTTS":

        return goles_local > 0 and goles_visitante > 0

    # ======================
    # CORNERS
    # ======================
    if "Corners Over" in market:

        try:

            linea = float(
                market.replace("Corners Over ", "")
            )

            stats = fixture.get("statistics", [])

            total_corners = 0

            for equipo in stats:

                for s in equipo["statistics"]:

                    if s["type"] == "Corner Kicks":

                        if s["value"] is not None:
                            total_corners += int(s["value"])

            return total_corners > linea

        except:
            return False

    return False

# =========================
# MAIN
# =========================
def main():

    ruta_csv = os.path.join(
        os.path.dirname(__file__),
        "..",
        "picks.csv"
    )

    if not os.path.exists(ruta_csv):
        print("❌ No existe picks.csv")
        return

    rows_actualizadas = []

    profit_total = 0
    ganadas = 0
    perdidas = 0

    # =========================
    # EVITAR DUPLICADOS
    # =========================
    procesados = set()

    with open(ruta_csv, "r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            # =========================
            # CLAVE UNICA
            # =========================
            clave = (
                row["fixture_id"],
                row["mercado"]
            )

            # Ya procesada
            if clave in procesados:
                continue

            procesados.add(clave)

            # Ya revisada
            if row["resultado"] != "pendiente":
                rows_actualizadas.append(row)
                continue

            fixture_id = row["fixture_id"]

            fixture = obtener_fixture(fixture_id)

            if not fixture:
                rows_actualizadas.append(row)
                continue

            estado = fixture["fixture"]["status"]["short"]

            # Partido no terminado
            if estado != "FT":
                rows_actualizadas.append(row)
                continue

            gano = verificar_pick(row, fixture)

            stake = float(row["stake"])
            odd = float(row["odd"])

            if gano:

                profit = round((stake * odd) - stake, 2)

                row["resultado"] = "ganada"
                row["profit"] = profit

                ganadas += 1
                profit_total += profit

            else:

                profit = round(-stake, 2)

                row["resultado"] = "perdida"
                row["profit"] = profit

                perdidas += 1
                profit_total += profit

            rows_actualizadas.append(row)

    # =========================
    # GUARDAR CSV
    # =========================
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
        "profit"
    ]

    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=campos
        )

        writer.writeheader()

        for r in rows_actualizadas:
            writer.writerow(r)

    # =========================
    # TELEGRAM
    # =========================
    if ganadas > 0 or perdidas > 0:

        mensaje = (
            "📊 RESULTADOS DEL BOT 📊\n\n"
            f"✅ Ganadas: {ganadas}\n"
            f"❌ Perdidas: {perdidas}\n"
            f"💰 Profit: {round(profit_total,2)}\n"
        )

        enviar_telegram(mensaje)

    else:
        print("⚠️ No hay picks terminadas")

# =========================
# START
# =========================
if __name__ == "__main__":
    main()