import requests
import csv
import os
import tempfile
import shutil

# =========================
# TELEGRAM
# =========================

TOKEN = "8393109030:AAGLfsuMveQXITjYSF8JJdmvs1-7AuLiq_E"
CHAT_ID = "-1003902179873"

# =========================
# RUTAS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICKS_PATH = os.path.join(BASE_DIR, "picks.csv")

# =========================
# ENVIAR MENSAJE
# =========================

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

            print("✅ Telegram enviado")
            return True

        else:

            print("❌ Error Telegram")
            return False

    except Exception as e:

        print("❌ Error enviando Telegram:", e)
        return False


# =========================
# NORMALIZAR TEXTO
# =========================

def normalizar(valor):

    if valor is None:
        return ""

    return str(valor).strip().lower()


# =========================
# CONVERTIR A FLOAT SEGURO
# =========================

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


# =========================
# CREAR ID UNICO DE PICK
# =========================

def pick_key(row):

    return (
        str(row.get("fixture_id", "")).strip(),
        str(row.get("partido", "")).strip(),
        str(row.get("mercado", "")).strip(),
        str(row.get("odd", "")).strip()
    )


# =========================
# GUARDAR CSV SEGURO
# =========================

def guardar_csv_seguro(rows, fieldnames):

    carpeta = os.path.dirname(PICKS_PATH)

    fd, temp_path = tempfile.mkstemp(
        dir=carpeta,
        suffix=".csv"
    )

    os.close(fd)

    try:

        with open(
            temp_path,
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
            writer.writerows(rows)

        shutil.move(temp_path, PICKS_PATH)

    except Exception as e:

        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise e


# =========================
# ENVIAR PICKS
# =========================

def enviar_picks():

    try:

        if not os.path.exists(PICKS_PATH):

            print("❌ No existe picks.csv")
            return

        with open(
            PICKS_PATH,
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = list(reader)

        if not rows:

            print("⚠️ picks.csv está vacío")
            return

        # Asegurar columna notificado
        if "notificado" not in fieldnames:
            fieldnames.append("notificado")

        picks_validas = []

        for row in rows:

            try:

                odd = to_float(row.get("odd", 0))
                score = to_float(row.get("score", 0))

                resultado = normalizar(row.get("resultado", ""))
                notificado = normalizar(row.get("notificado", ""))

                # SOLO PICKS PENDIENTES
                if resultado != "pendiente":
                    continue

                # NO REPETIR PICKS YA ENVIADAS
                if notificado == "si":
                    continue

                # FILTRO DE SEGURIDAD COHERENTE CON MAIN.PY
                # MAIN.PY YA FILTRA SCORE >= 18
                if (
                    odd > 0
                    and score >= 18
                ):

                    picks_validas.append(row)

            except Exception as e:

                print("⚠️ Fila ignorada:", e)
                continue

        # =========================
        # ORDENAR PICKS
        # =========================

        picks_validas = sorted(
            picks_validas,
            key=lambda x: to_float(x.get("score", 0)),
            reverse=True
        )[:10]

        # =========================
        # NO HAY PICKS NUEVAS
        # =========================

        if not picks_validas:

            print("⚠️ No hay picks nuevas para enviar")
            return

        # =========================
        # MENSAJE
        # =========================

        mensaje = "🔥 PICKS TOP DEL BOT 🔥\n\n"

        for row in picks_validas:

            mensaje += (
                f"🔥 PICK TOP 🔥\n"
                f"⚽ {row.get('partido', '-')}\n"
                f"🏆 {row.get('liga', '-')}\n"
                f"📅 Partido: {row.get('fecha', '-')[:16]}\n"
                f"👉 {row.get('mercado', '-')}\n"
                f"💰 Odds: {row.get('odd', '-')}\n"
                f"📊 Prob: {row.get('prob', '-')}\n"
                f"🔥 Value: {row.get('value', '-')}\n"
                f"⭐ Score: {row.get('score', '-')}\n"
                f"💵 Stake: {row.get('stake', '-')}\n\n"
            )

        print(f"📨 Picks nuevas a enviar: {len(picks_validas)}")

        enviado = enviar_mensaje(mensaje)

        if not enviado:

            print("❌ No se marcaron como notificadas porque Telegram falló")
            return

        # =========================
        # MARCAR COMO NOTIFICADAS
        # =========================

        keys_enviadas = set(
            pick_key(row)
            for row in picks_validas
        )

        marcadas = 0

        for row in rows:

            if pick_key(row) in keys_enviadas:

                row["notificado"] = "si"
                marcadas += 1

        guardar_csv_seguro(rows, fieldnames)

        print(f"✅ Picks marcadas como notificadas: {marcadas}")

    except Exception as e:

        print("❌ ERROR GENERAL:", e)


# =========================
# START
# =========================

if __name__ == "__main__":

    enviar_picks()