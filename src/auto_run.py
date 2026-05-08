import time
import subprocess
from datetime import datetime

# =========================
# CONTROL EJECUCION
# =========================

ultimas_horas = []

while True:

    print("\n============================")
    print("⏰ BOT ACTIVO:", datetime.now())
    print("============================")

    ahora = datetime.now()

    hoy = ahora.date()
    hora_actual = ahora.hour

    # =========================
    # HORARIOS DE PICKS
    # =========================
    # 5 AM
    # 10 AM
    # 5 PM
    # 8 PM

    horarios = [5, 10, 17, 20]

    clave = f"{hoy}_{hora_actual}"

    if (
        hora_actual in horarios
        and clave not in ultimas_horas
    ):

        print("📊 Generando picks...")

        subprocess.run([
            "python",
            "src/main.py"
        ])

        print("📨 Enviando Telegram...")

        subprocess.run([
            "python",
            "enviar_telegram.py"
        ])

        ultimas_horas.append(clave)

        print("✅ Picks enviados")

    # =========================
    # ACTUALIZAR RESULTADOS
    # =========================

    try:

        print("🔄 Actualizando resultados...")

        subprocess.run([
            "python",
            "src/actualizar_resultados.py"
        ])

    except:
        print("⚠️ No se pudieron actualizar resultados")

    # =========================
    # ESPERA
    # =========================

    print("⏳ Esperando 20 minutos...\n")

    time.sleep(1200)