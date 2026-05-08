import subprocess
import threading
import time

# 🔥 iniciar bot automatico
def iniciar_bot():

    while True:

        print("🔥 Ejecutando auto_run.py...")

        proceso = subprocess.Popen(
            ["python", "src/auto_run.py"]
        )

        proceso.wait()

        print("⚠️ auto_run terminado. Reiniciando en 10 segundos...")

        time.sleep(10)


# 🔥 arrancar hilo del bot
threading.Thread(target=iniciar_bot, daemon=True).start()


# 🔥 iniciar dashboard
from src.dashboard.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)