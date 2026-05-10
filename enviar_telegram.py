import requests
import csv
import os

# =========================
# TELEGRAM
# =========================

TOKEN = "8393109030:AAGLfsuMveQXITjYSF8JJdmvs1-7AuLiq_E"
CHAT_ID = "-1003902179873"

# =========================
# ENVIAR MENSAJE
# =========================

def enviar_mensaje(texto):

    try:

        url = (
            f"https://api.telegram.org/bot"
            f"{TOKEN}/sendMessage"
        )

        data = {
            "chat_id": CHAT_ID,
            "text": texto
        }

        r = requests.post(
            url,
            data=data,
            timeout=20
        )

        print(r.text)

        if r.status_code == 200:

            print("✅ Telegram enviado")

        else:

            print("❌ Error Telegram")

    except Exception as e:

        print("❌ Error:", e)

# =========================
# ENVIAR PICKS
# =========================

def enviar_picks():

    try:

        ruta = os.path.join(
            os.path.dirname(__file__),
            "picks.csv"
        )

        if not os.path.exists(ruta):

            print("❌ No existe picks.csv")
            return

        with open(
            ruta,
            newline='',
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            picks_validas = []

            for row in reader:

                try:

                    value = float(row['value'])
                    prob = float(row['prob'])
                    odd = float(row['odd'])

                    # SOLO PICKS PENDIENTES
                    if row["resultado"] != "pendiente":
                        continue

                    # FILTRO PICKS
                    if (
                        value >= 0.01
                        and prob >= 0.40
                        and odd <= 3.5
                    ):

                        picks_validas.append(row)

                except:
                    continue

            # =========================
            # ORDENAR PICKS
            # =========================

            picks_validas = sorted(

                picks_validas,

                key=lambda x: float(x["value"]),

                reverse=True

            )[:10]

            # =========================
            # NO HAY PICKS
            # =========================

            if not picks_validas:

                print("⚠️ No hay picks válidas")

                enviar_mensaje(
                    "❌ No hay picks de valor hoy"
                )

                return

            # =========================
            # MENSAJE
            # =========================

            mensaje = (
                "🔥 PICKS TOP DEL BOT 🔥\n\n"
            )

            for row in picks_validas:

                mensaje += (

                    f"🔥 PICK TOP 🔥\n"
                    f"⚽ {row['partido']}\n"
                    f"🏆 {row['liga']}\n"
                    f"📅 {row['fecha'][:16]}\n"
                    f"👉 {row['mercado']}\n"
                    f"💰 Odds: {row['odd']}\n"
                    f"📊 Prob: {row['prob']}\n"
                    f"🔥 Value: {row['value']}\n"
                    f"💵 Stake: {row['stake']}\n\n"
                )

            print(
                f"📨 Picks enviadas: {len(picks_validas)}"
            )

            enviar_mensaje(
                mensaje
            )

    except Exception as e:

        print("❌ ERROR GENERAL:", e)

# =========================
# START
# =========================

if __name__ == "__main__":

    enviar_picks()