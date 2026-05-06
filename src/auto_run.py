import time
import subprocess
from datetime import datetime

ultima_ejecucion_picks = None

while True:
    print("\n============================")
    print("⏰ BOT ACTIVO:", datetime.now())
    print("============================")

    ahora = datetime.now()

    # picks 1 vez al día (8 AM)
    if ultima_ejecucion_picks is None or ahora.hour == 8:
        print("📊 Generando picks...")
        subprocess.run(["python", "main.py"])
        ultima_ejecucion_picks = ahora

    print("🔄 Actualizando resultados...")
    subprocess.run(["python", "actualizar_resultados.py"])

    print("⏳ Esperando 20 minutos...\n")
    time.sleep(1200)