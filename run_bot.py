import threading
import subprocess
from src.dashboard.app import app

# =========================
# BOT
# =========================

def iniciar_bot():

    try:

        subprocess.run([
            "python",
            "src/auto_run.py"
        ])

    except Exception as e:

        print("ERROR BOT:", e)

# =========================
# HILO
# =========================

bot_thread = threading.Thread(
    target=iniciar_bot
)

bot_thread.daemon = True
bot_thread.start()

# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )