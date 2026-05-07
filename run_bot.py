import subprocess
import threading
from flask import Flask

app = Flask(__name__)

def iniciar_bot():

    print("🚀 Iniciando sistema...")

    try:

        # SOLO ejecuta auto_run.py
        subprocess.run([
            "python",
            "src/auto_run.py"
        ])

    except Exception as e:

        print(f"❌ Error: {e}")

# =========================
# HILO BOT
# =========================

threading.Thread(
    target=iniciar_bot
).start()

# =========================
# WEB RENDER
# =========================

@app.route("/")
def home():

    return "✅ Bot funcionando"

# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )