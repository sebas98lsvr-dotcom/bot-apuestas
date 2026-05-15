import csv
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ======================
# ENV
# ======================

BASE_DIR = os.path.dirname(__file__)

ruta_env = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ruta_env)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ======================
# RUTAS
# ======================

ruta_picks = os.path.join(
    BASE_DIR,
    "picks.csv"
)

ruta_control = os.path.join(
    BASE_DIR,
    "resumen_diario_enviado.txt"
)

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
            print("✅ Resumen diario enviado a Telegram")
            return True

        print("⚠️ Telegram status:", r.status_code)
        print(r.text)
        return False

    except Exception as e:

        print("❌ Error Telegram:", e)
        return False


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


def obtener_fecha_de_pick(valor_fecha):

    try:
        texto = limpiar_texto(valor_fecha)

        if not texto:
            return ""

        # Formato típico:
        # 2026-05-15 13:00
        # 2026-05-15 13:00:00
        # 2026-05-15 13:00:00.000000

        return texto[:10]

    except:
        return ""


def ya_se_envio_resumen(fecha_hoy):

    if not os.path.exists(ruta_control):
        return False

    try:
        with open(ruta_control, "r", encoding="utf-8") as f:
            contenido = f.read().strip()

        return contenido == fecha_hoy

    except:
        return False


def marcar_resumen_enviado(fecha_hoy):

    with open(ruta_control, "w", encoding="utf-8") as f:
        f.write(fecha_hoy)


def calcular_mejor_peor_mercado(picks_cerradas):

    mercados = {}

    for p in picks_cerradas:

        mercado = limpiar_texto(
            p.get("mercado", "Sin mercado")
        )

        profit = to_float(
            p.get("profit", 0),
            0
        )

        if mercado not in mercados:
            mercados[mercado] = {
                "profit": 0.0,
                "picks": 0,
                "wins": 0,
                "losses": 0
            }

        mercados[mercado]["profit"] += profit
        mercados[mercado]["picks"] += 1

        resultado = limpiar_texto(
            p.get("resultado", "")
        ).lower()

        if resultado == "win":
            mercados[mercado]["wins"] += 1

        elif resultado == "loss":
            mercados[mercado]["losses"] += 1

    if not mercados:
        return "N/A", "N/A"

    mejor = max(
        mercados.items(),
        key=lambda x: x[1]["profit"]
    )

    peor = min(
        mercados.items(),
        key=lambda x: x[1]["profit"]
    )

    mejor_texto = (
        f"{mejor[0]} "
        f"({round(mejor[1]['profit'], 2)} profit)"
    )

    peor_texto = (
        f"{peor[0]} "
        f"({round(peor[1]['profit'], 2)} profit)"
    )

    return mejor_texto, peor_texto


# ======================
# PROCESO PRINCIPAL
# ======================

def main():

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    if ya_se_envio_resumen(fecha_hoy):
        print("ℹ️ El resumen diario ya fue enviado hoy.")
        return

    if not os.path.exists(ruta_picks):
        print("⚠️ No existe picks.csv")
        return

    picks = []

    with open(
        ruta_picks,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if not any(
                str(v).strip()
                for v in row.values()
                if v is not None
            ):
                continue

            picks.append(row)

    if not picks:
        print("⚠️ No hay picks en picks.csv")
        return

    # Picks del día actual
    picks_hoy = []

    for p in picks:

        fecha_pick = obtener_fecha_de_pick(
            p.get("fecha", "")
        )

        if fecha_pick == fecha_hoy:
            picks_hoy.append(p)

    if not picks_hoy:

        mensaje = (
            "📊 RESUMEN DIARIO DEL BOT\n\n"
            f"📅 Fecha: {fecha_hoy}\n\n"
            "ℹ️ Hoy no hubo picks registradas."
        )

        enviado = enviar_telegram(mensaje)

        if enviado:
            marcar_resumen_enviado(fecha_hoy)

        return

    picks_cerradas = []
    picks_pendientes = []

    for p in picks_hoy:

        resultado = limpiar_texto(
            p.get("resultado", "")
        ).lower()

        if resultado in ["win", "loss"]:
            picks_cerradas.append(p)

        elif resultado == "pendiente":
            picks_pendientes.append(p)

    wins = sum(
        1 for p in picks_cerradas
        if limpiar_texto(p.get("resultado", "")).lower() == "win"
    )

    losses = sum(
        1 for p in picks_cerradas
        if limpiar_texto(p.get("resultado", "")).lower() == "loss"
    )

    total_cerradas = wins + losses
    total_pendientes = len(picks_pendientes)
    total_picks_hoy = len(picks_hoy)

    profit_total = sum(
        to_float(p.get("profit", 0), 0)
        for p in picks_cerradas
    )

    stake_total = sum(
        to_float(p.get("stake", 0), 0)
        for p in picks_cerradas
    )

    if total_cerradas > 0:
        winrate = round(
            (wins / total_cerradas) * 100,
            2
        )
    else:
        winrate = 0.0

    if stake_total > 0:
        roi = round(
            (profit_total / stake_total) * 100,
            2
        )
    else:
        roi = 0.0

    mejor_mercado, peor_mercado = calcular_mejor_peor_mercado(
        picks_cerradas
    )

    signo_profit = "+" if profit_total > 0 else ""

    if profit_total > 0:
        estado_dia = "🟢 Día positivo"
    elif profit_total < 0:
        estado_dia = "🔴 Día negativo"
    else:
        estado_dia = "⚪ Día neutro"

    mensaje = (
        "📊 RESUMEN DIARIO DEL BOT\n\n"
        f"📅 Fecha: {fecha_hoy}\n"
        f"{estado_dia}\n\n"
        f"🎯 Picks totales hoy: {total_picks_hoy}\n"
        f"✅ Picks cerradas: {total_cerradas}\n"
        f"⏳ Picks pendientes: {total_pendientes}\n\n"
        f"🟢 Ganadas: {wins}\n"
        f"🔴 Perdidas: {losses}\n"
        f"📈 Winrate: {winrate}%\n\n"
        f"💵 Stake cerrado: {round(stake_total, 2)}\n"
        f"💰 Profit del día: {signo_profit}{round(profit_total, 2)}\n"
        f"📊 ROI diario: {roi}%\n\n"
        f"🏆 Mejor mercado: {mejor_mercado}\n"
        f"⚠️ Peor mercado: {peor_mercado}"
    )

    enviado = enviar_telegram(mensaje)

    if enviado:
        marcar_resumen_enviado(fecha_hoy)


if __name__ == "__main__":
    main()