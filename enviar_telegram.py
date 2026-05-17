import os
import csv
import requests
from dotenv import load_dotenv

# ==============================
# CARGAR ENV
# ==============================

ruta_env = os.path.join(
    os.path.dirname(__file__),
    ".env"
)

load_dotenv(ruta_env)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==============================
# RUTAS
# ==============================

RUTA_PICKS = os.path.join(
    os.path.dirname(__file__),
    "picks.csv"
)

# ==============================
# VALIDAR CONFIG TELEGRAM
# ==============================

def telegram_config_ok():

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no están configurados en .env")
        return False

    return True

# ==============================
# CONVERTIR FLOAT SEGURO
# ==============================

def to_float(valor, default=0):

    try:

        if valor is None:
            return default

        valor = str(valor).replace(",", ".").strip()

        if valor == "":
            return default

        return float(valor)

    except Exception:

        return default

# ==============================
# VALIDAR PICK ENVIABLE
# ==============================

def pick_es_enviable(row):

    mercado = str(
        row.get("mercado", "")
    ).strip()

    partido = str(
        row.get("partido", "")
    ).strip()

    score = to_float(
        row.get("score", 0)
    )

    odd = to_float(
        row.get("odd", 0)
    )

    prob = to_float(
        row.get("prob", 0)
    )

    value = to_float(
        row.get("value", 0)
    )

    notificado = str(
        row.get("notificado", "")
    ).strip().lower()

    resultado = str(
        row.get("resultado", "")
    ).strip().lower()

    contexto = str(
        row.get("contexto", "")
    ).strip()

    # ==============================
    # YA NOTIFICADO
    # ==============================

    if notificado == "si":
        return False, "Pick ya notificada"

    # ==============================
    # SOLO PENDIENTES
    # ==============================

    if resultado != "pendiente":
        return False, f"Resultado no pendiente: {resultado}"

    # ==============================
    # MERCADOS ACTIVOS
    # ==============================

    if mercado not in ["Over 1.5", "Over 2.5", "BTTS"]:
        return False, f"Mercado desactivado temporalmente: {mercado}"

    # ==============================
    # VALIDACIONES GENERALES
    # ==============================

    if partido == "":
        return False, "Partido vacío"

    if odd <= 1.20:
        return False, f"Odd demasiado baja: {odd}"

    if prob <= 0:
        return False, f"Probabilidad inválida: {prob}"

    if value <= 0:
        return False, f"Value inválido: {value}"

    if score <= 0:
        return False, f"Score inválido: {score}"

    # ==============================
    # FILTROS OVER 2.5
    # ==============================

    if mercado == "Over 2.5":

        if score < 25:
            return False, f"Over 2.5 con score menor a 25: {score}"

        if odd < 1.60:
            return False, f"Over 2.5 con odd baja: {odd}"

        if prob < 0.70:
            return False, f"Over 2.5 con probabilidad menor a 0.70: {prob}"

        if "OK Over25" not in contexto:
            return False, "Over 2.5 sin contexto OK Over25"

    # ==============================
    # FILTROS OVER 1.5
    # ==============================

    if mercado == "Over 1.5":

        if score < 19:
            return False, f"Over 1.5 con score menor a 19: {score}"

        if odd < 1.30:
            return False, f"Over 1.5 con odd demasiado baja: {odd}"

        if prob < 0.88:
            return False, f"Over 1.5 con probabilidad menor a 0.88: {prob}"

        if "OK Over15" not in contexto:
            return False, "Over 1.5 sin contexto OK Over15"

    # ==============================
    # FILTROS BTTS EXIGENTES
    # ==============================

    if mercado == "BTTS":

        # Score mínimo fuerte
        if score < 23:
            return False, f"BTTS con score menor a 23: {score}"

        # Odd mínima para que valga la pena
        if odd < 1.65:
            return False, f"BTTS con odd menor a 1.65: {odd}"

        # Evitar cuotas demasiado altas/riesgosas
        if odd > 2.35:
            return False, f"BTTS con odd demasiado alta: {odd}"

        # Probabilidad mínima exigente
        if prob < 0.64:
            return False, f"BTTS con probabilidad menor a 0.64: {prob}"

        # Value mínimo real
        if value < 0.04:
            return False, f"BTTS con value menor a 0.04: {value}"

        # Debe venir aprobado desde main.py por contexto
        if "OK BTTS" not in contexto:
            return False, "BTTS sin contexto OK BTTS"

        # Seguridad extra:
        # si el contexto no trae señales de goles a favor/contra,
        # mejor no enviarlo.
        if "Home GF" not in contexto or "Away GF" not in contexto:
            return False, "BTTS sin datos GF en contexto"

        if "Home GC" not in contexto or "Away GC" not in contexto:
            return False, "BTTS sin datos GC en contexto"

    return True, "OK"

# ==============================
# FORMATEAR MENSAJE
# ==============================

def formatear_mensaje(picks):

    mensaje = "🔥 PICKS TOP DEL BOT 🔥\n\n"

    for p in picks:

        fecha = p.get("fecha", "")
        partido = p.get("partido", "")
        liga = p.get("liga", "")
        mercado = p.get("mercado", "")
        odd = p.get("odd", "")
        prob = p.get("prob", "")
        value = p.get("value", "")
        score = p.get("score", "")
        stake = p.get("stake", "")
        contexto = p.get("contexto", "")

        mensaje += "🔥 PICK TOP 🔥\n"
        mensaje += f"⚽ {partido}\n"
        mensaje += f"🏆 {liga}\n"
        mensaje += f"📅 Partido: {fecha}\n"
        mensaje += f"🎯 Mercado: {mercado}\n"
        mensaje += f"💰 Odd: {odd}\n"
        mensaje += f"📊 Prob: {prob}\n"
        mensaje += f"📈 Value: {value}\n"
        mensaje += f"⭐ Score: {score}\n"
        mensaje += f"💵 Stake sugerido: {stake}\n"

        if contexto:
            mensaje += f"🧠 Contexto: {contexto}\n"

        mensaje += "\n"

    mensaje += "⚠️ Apuesta con gestión de bank. No es garantía de resultado."

    return mensaje

# ==============================
# ENVIAR MENSAJE TELEGRAM
# ==============================

def enviar_mensaje_telegram(mensaje):

    url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }

    try:

        r = requests.post(
            url,
            data=data,
            timeout=20
        )

        print("📨 Telegram status:", r.status_code)

        if r.status_code != 200:
            print("❌ Respuesta Telegram:", r.text)
            return False

        return True

    except Exception as e:

        print("❌ Error enviando Telegram:", e)
        return False

# ==============================
# LEER PICKS
# ==============================

def leer_picks():

    if not os.path.exists(RUTA_PICKS):
        print("⚠️ No existe picks.csv")
        return []

    with open(
        RUTA_PICKS,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        return list(reader)

# ==============================
# GUARDAR PICKS ACTUALIZADAS
# ==============================

def guardar_picks(rows, fieldnames):

    with open(
        RUTA_PICKS,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

# ==============================
# MAIN
# ==============================

def main():

    if not telegram_config_ok():
        print("❌ No se marcarán picks como notificadas porque Telegram falló")
        return

    rows = leer_picks()

    if not rows:
        print("⚠️ No hay picks para revisar")
        return

    fieldnames = list(rows[0].keys())

    picks_enviables = []

    for row in rows:

        ok, razon = pick_es_enviable(row)

        if ok:
            picks_enviables.append(row)
        else:
            partido = row.get("partido", "")
            mercado = row.get("mercado", "")
            print(
                f"⏭️ No enviada: {partido} | {mercado} | {razon}"
            )

    if not picks_enviables:
        print("⚠️ No hay picks nuevas enviables")
        return

    mensaje = formatear_mensaje(
        picks_enviables
    )

    enviado = enviar_mensaje_telegram(
        mensaje
    )

    if not enviado:
        print("❌ No se marcarán picks como notificadas porque Telegram falló")
        return

    ids_enviados = set()

    for p in picks_enviables:

        clave = (
            str(p.get("fixture_id", ""))
            + "_"
            + str(p.get("mercado", ""))
        )

        ids_enviados.add(clave)

    for row in rows:

        clave = (
            str(row.get("fixture_id", ""))
            + "_"
            + str(row.get("mercado", ""))
        )

        if clave in ids_enviados:
            row["notificado"] = "si"

    guardar_picks(
        rows,
        fieldnames
    )

    print(
        f"✅ Picks enviadas y marcadas como notificadas: {len(picks_enviables)}"
    )

# ==============================
# START
# ==============================

if __name__ == "__main__":

    main()