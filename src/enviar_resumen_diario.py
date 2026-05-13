import csv
import os
import requests
from datetime import datetime
import pytz

# =========================
# TELEGRAM
# =========================

TOKEN = "8393109030:AAGLfsuMveQXITjYSF8JJdmvs1-7AuLiq_E"
CHAT_ID = "-1003902179873"

# =========================
# RUTAS
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICKS_PATH = os.path.join(BASE_DIR, "picks.csv")
CONTROL_PATH = os.path.join(BASE_DIR, "resumen_diario_enviado.txt")

# =========================
# HELPERS
# =========================

def normalizar(valor):
    if valor is None:
        return ""
    return str(valor).strip().lower()


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


def parse_fecha(fecha_str):
    try:
        fecha_str = str(fecha_str).strip()

        if not fecha_str:
            return None

        # Soporta: 2026-05-14 14:40
        try:
            return datetime.strptime(fecha_str[:16], "%Y-%m-%d %H:%M")
        except:
            pass

        # Soporta: 2026-05-11 12:37:50.809255
        try:
            return datetime.strptime(fecha_str[:19], "%Y-%m-%d %H:%M:%S")
        except:
            pass

        return None

    except:
        return None


def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

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
            print("✅ Resumen diario enviado")
            return True
        else:
            print("❌ Error enviando resumen diario")
            return False

    except Exception as e:
        print("❌ Error Telegram:", e)
        return False


def resumen_ya_enviado(hoy_str):
    if not os.path.exists(CONTROL_PATH):
        return False

    try:
        with open(CONTROL_PATH, "r", encoding="utf-8") as f:
            contenido = f.read().strip()

        return contenido == hoy_str

    except:
        return False


def marcar_resumen_enviado(hoy_str):
    with open(CONTROL_PATH, "w", encoding="utf-8") as f:
        f.write(hoy_str)


# =========================
# RESUMEN DIARIO
# =========================

def enviar_resumen_diario():

    zona_colombia = pytz.timezone("America/Bogota")
    ahora = datetime.now(zona_colombia)
    hoy = ahora.date()
    hoy_str = hoy.strftime("%Y-%m-%d")

    if resumen_ya_enviado(hoy_str):
        print("⚠️ El resumen diario ya fue enviado hoy")
        return

    if not os.path.exists(PICKS_PATH):
        print("❌ No existe picks.csv")
        return

    with open(
        PICKS_PATH,
        newline="",
        encoding="utf-8"
    ) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    picks_hoy = []

    for row in rows:

        fecha = parse_fecha(row.get("fecha", ""))

        if fecha is None:
            continue

        # Resumen por fecha en que el bot generó/guardó la pick
        if fecha.date() == hoy:
            picks_hoy.append(row)

    if not picks_hoy:

        mensaje = (
            "📊 RESUMEN DIARIO DATABETAI\n\n"
            f"📅 Fecha: {hoy_str}\n\n"
            "Hoy no se generaron picks para resumir.\n\n"
            "🔥 Seguimos buscando value."
        )

        enviado = enviar_mensaje(mensaje)

        if enviado:
            marcar_resumen_enviado(hoy_str)

        return

    ganadas = [
        p for p in picks_hoy
        if normalizar(p.get("resultado", "")) == "win"
    ]

    perdidas = [
        p for p in picks_hoy
        if normalizar(p.get("resultado", "")) == "loss"
    ]

    pendientes = [
        p for p in picks_hoy
        if normalizar(p.get("resultado", "")) == "pendiente"
    ]

    finalizadas = ganadas + perdidas

    total = len(picks_hoy)
    total_ganadas = len(ganadas)
    total_perdidas = len(perdidas)
    total_pendientes = len(pendientes)

    profit_total = sum(
        to_float(p.get("profit", 0))
        for p in picks_hoy
    )

    stake_total = sum(
        to_float(p.get("stake", 0))
        for p in picks_hoy
    )

    winrate = 0

    if len(finalizadas) > 0:
        winrate = (total_ganadas / len(finalizadas)) * 100

    roi = 0

    if stake_total > 0:
        roi = (profit_total / stake_total) * 100

    mejor_pick = None

    if finalizadas:
        mejor_pick = max(
            finalizadas,
            key=lambda x: to_float(x.get("profit", 0))
        )

    mensaje = (
        "📊 RESUMEN DIARIO DATABETAI\n\n"
        f"📅 Fecha: {hoy_str}\n\n"
        f"🎯 Picks generadas hoy: {total}\n"
        f"🟢 Ganadas: {total_ganadas}\n"
        f"🔴 Perdidas: {total_perdidas}\n"
        f"🟡 Pendientes: {total_pendientes}\n\n"
        f"📈 Winrate finalizadas: {winrate:.1f}%\n"
        f"💰 Profit parcial: {profit_total:.1f} unidades\n"
        f"🏦 Stake total: {stake_total:.1f} unidades\n"
        f"📊 ROI parcial: {roi:.1f}%\n"
    )

    if mejor_pick:

        mensaje += (
            "\n🔥 Mejor pick finalizada:\n"
            f"⚽ {mejor_pick.get('partido', '-')}\n"
            f"🏆 {mejor_pick.get('liga', '-')}\n"
            f"👉 {mejor_pick.get('mercado', '-')}\n"
            f"📌 Score: {mejor_pick.get('score', '-')}\n"
            f"💰 Profit: {to_float(mejor_pick.get('profit', 0)):.1f}\n"
        )

    mensaje += (
        "\n🚀 DataBetAI sigue buscando picks...."
    )

    enviado = enviar_mensaje(mensaje)

    if enviado:
        marcar_resumen_enviado(hoy_str)


# =========================
# START
# =========================

if __name__ == "__main__":
    enviar_resumen_diario()