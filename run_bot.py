import subprocess
import threading
import time
import sys

# 🔥 iniciar bot automatico
def iniciar_bot():

    while True:

        try:

            print("🔥 Ejecutando auto_run.py...")

            proceso = subprocess.Popen(
            [sys.executable, "-u", "src/auto_run.py"]
            )

            proceso.wait()

            print("⚠️ auto_run terminado. Reiniciando en 10 segundos...")

        except Exception as e:

            print(f"❌ Error ejecutando auto_run.py: {e}")

        time.sleep(10)


# 🔥 arrancar hilo del bot
threading.Thread(target=iniciar_bot, daemon=True).start()


# 🔥 iniciar dashboard
from src.dashboard.app import app

if __name__ == "__main__":

    print("🚀 Iniciando dashboard Flask...")

    app.run(
        host="0.0.0.0",
        port=10000
    )