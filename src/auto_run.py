import time
import subprocess
import sys
from datetime import datetime

# =========================
# CONTROL EJECUCION
# =========================

ultimas_horas = []

print("🚀 AUTO_RUN INICIADO")

while True:

    try:

        print("\n============================")
        print("⏰ BOT ACTIVO:", datetime.now())
        print("============================")

        ahora = datetime.now()

        hoy = ahora.date()
        hora_actual = ahora.hour

        # =========================
        # HORARIOS DE PICKS
        # =========================

        horarios = [5, 10, 17, 20]

        clave = f"{hoy}_{hora_actual}"

        if (
            hora_actual in horarios
            and clave not in ultimas_horas
        ):

            print("📊 Generando picks...")

            subprocess.run([
                sys.executable,
                "src/main.py"
            ])

            print("📨 Enviando Telegram...")

            subprocess.run([
                sys.executable,
                "enviar_telegram.py"
            ])

            ultimas_horas.append(clave)

            print("✅ Picks enviados")

        else:

            print("⌛ No es hora de enviar picks todavía")

        # =========================
        # ACTUALIZAR RESULTADOS
        # =========================

        try:

            print("🔄 Actualizando resultados...")

            subprocess.run([
                sys.executable,
                "src/actualizar_resultados.py"
            ])

            print("✅ Resultados actualizados")

        except Exception as e:

            print(f"⚠️ Error actualizando resultados: {e}")

    except Exception as e:

        print(f"❌ ERROR GENERAL: {e}")

    # =========================
    # ESPERA
    # =========================

    print("⏳ Esperando 20 minutos...\n")

    time.sleep(1200)