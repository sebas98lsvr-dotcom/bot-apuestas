import time
import subprocess
from datetime import datetime

# =========================
# CONTROL EJECUCION
# =========================

ultimo_dia_picks = None

while True:

    print("\n============================")
    print("⏰ BOT ACTIVO:", datetime.now())
    print("============================")

    ahora = datetime.now()

    # =========================
    # PICKS SOLO 1 VEZ AL DIA
    # =========================

    hoy = ahora.date()

    if (
        ahora.hour == 12
        and ultimo_dia_picks != hoy
    ):

        print("📊 Generando picks...")

        subprocess.run([
            "python",
            "main.py"
        ])

        ultimo_dia_picks = hoy

    # =========================
    # ACTUALIZAR RESULTADOS
    # =========================

    # TEMPORALMENTE DESACTIVADO
    # porque el archivo no existe

    # subprocess.run([
    #     "python",
    #     "actualizar_resultados.py"
    # ])

    # =========================
    # ESPERA
    # =========================

    print("⏳ Esperando 20 minutos...\n")

    time.sleep(1200)
