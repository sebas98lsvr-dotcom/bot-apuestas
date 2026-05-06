import requests
import csv

TOKEN = "8393109030:AAGLfsuMveQXITjYSF8JJdmvs1-7AuLiq_E"
CHAT_ID = "-1003902179873"

def enviar_mensaje(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": texto
    }
    r = requests.post(url, data=data)
    print(r.text)

def enviar_picks():
    try:
        with open("picks.csv", newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)

            mensaje = "🔥 PICKS TOP DEL BOT 🔥\n\n"
            hay_picks = False

            for row in reader:
                value = float(row['value'])
                prob = float(row['prob'])
                odd = float(row['odd'])

                # 🔥 FILTRO PROFESIONAL
                if value >= 0.15 and prob >= 0.40 and odd <= 3.5:
                    hay_picks = True

                    mensaje += (
                        f"🔥 PICK TOP 🔥\n"
                        f"⚽ {row['partido']}\n"
                        f"👉 {row['mercado']}\n"
                        f"💰 Odds: {row['odd']}\n"
                        f"📊 Prob: {row['prob']}\n"
                        f"🔥 Value: {row['value']}\n"
                        f"💵 Stake: {row['stake']}\n\n"
                    )

            if not hay_picks:
                mensaje = "❌ No hay picks de valor hoy"

            enviar_mensaje(mensaje)

    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    enviar_picks()