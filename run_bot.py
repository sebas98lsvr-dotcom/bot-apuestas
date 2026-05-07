import subprocess
import threading
from flask import Flask
from src.dashboard.app import app as dashboard_app

app = dashboard_app

# =========================
# BOT
# =========================

def iniciar_bot():

    print("🚀 Iniciando sistema...")

    try:

        subprocess.run([
            "python",
            "src/auto_run.py"
        ])

    except Exception as e:

        print(f"❌ Error: {e}")

# =========================
# HILO
# =========================

threading.Thread(
    target=iniciar_bot
).start()

# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )