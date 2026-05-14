import time
import subprocess
import sys
import os
from datetime import datetime
import pytz

try:
    sys.stdout.reconfigure(line_buffering=True)
except:
    pass

# =========================
# RUTAS SEGURAS
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

MAIN_FILE = os.path.join(
    BASE_DIR,
    "src",
    "main.py"
)

ACTUALIZAR_FILE = os.path.join(
    BASE_DIR,
    "src",
    "actualizar_resultados.py"
)

TELEGRAM_FILE = os.path.join(
    BASE_DIR,
    "enviar_telegram.py"
)

# =========================
# CONTROL EJECUCION
# =========================

ultimas_horas = []

print("🚀 AUTO_RUN INICIADO")

while True:

    try:

        zona_colombia = pytz.timezone("America/Bogota")
        ahora = datetime.now(zona_colombia)

        print("\n============================")
        print("🤖 BOT ACTIVO:", ahora)
        print("============================")

        hoy = ahora.date()
        hora_actual = ahora.hour

        # =========================
        # HORARIOS DE PICKS
        # =========================

        horarios = [
            3,
            7,
            12,
            14,
            17,
            20
        ]

        clave = f"{hoy}_{hora_actual}"

        if (
            hora_actual in horarios
            and clave not in ultimas_horas
        ):

            print("📊 Generando picks...")

            subprocess.run(
                [
                    sys.executable,
                    MAIN_FILE
                ],
                cwd=BASE_DIR
            )

            print("📨 Enviando picks a Telegram...")

            subprocess.run(
                [
                    sys.executable,
                    TELEGRAM_FILE
                ],
                cwd=BASE_DIR
            )

            ultimas_horas.append(
                clave
            )

            # limpiar memoria de horas viejas
            if len(ultimas_horas) > 30:
                ultimas_horas = ultimas_horas[-30:]

            print("✅ Proceso de picks terminado")

        else:

            print("⌛ No es hora de generar picks todavía")

        # =========================
        # ACTUALIZAR RESULTADOS
        # =========================

        try:

            print("🔄 Actualizando resultados...")

            subprocess.run(
                [
                    sys.executable,
                    ACTUALIZAR_FILE
                ],
                cwd=BASE_DIR
            )

            print("✅ Revisión de resultados terminada")

        except Exception as e:

            print(f"⚠️ Error actualizando resultados: {e}")

        # =========================
        # ENVIAR PICKS PENDIENTES
        # =========================
        # Esto evita que picks creados manualmente con main.py
        # se queden en picks.csv con notificado = no.
        # No debería repetir porque enviar_telegram.py solo envía
        # resultado = pendiente y notificado != si.

        try:

            print("📨 Revisando picks pendientes para Telegram...")

            subprocess.run(
                [
                    sys.executable,
                    TELEGRAM_FILE
                ],
                cwd=BASE_DIR
            )

            print("✅ Revisión de Telegram terminada")

        except Exception as e:

            print(f"⚠️ Error enviando picks pendientes: {e}")

    except Exception as e:

        print(f"❌ ERROR GENERAL: {e}")

    # =========================
    # ESPERA
    # =========================

    print("⏳ Esperando 30 minutos...\n")

    time.sleep(1800)