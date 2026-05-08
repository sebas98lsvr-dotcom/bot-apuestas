import threading
import subprocess

# 🔥 iniciar bot automatico
def iniciar_bot():
    subprocess.Popen(["python", "src/auto_run.py"])

threading.Thread(target=iniciar_bot).start()

# 🔥 iniciar dashboard flask
from src.dashboard.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)