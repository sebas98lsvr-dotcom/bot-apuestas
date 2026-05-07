import subprocess
import time
import threading
from flask import Flask

app = Flask(__name__)

def iniciar_bot():
    print("🚀 Bot iniciado...")

    while True:
        try:
            print("⚽ Generando picks...")
            subprocess.run(["python", "src/main.py"])

            time.sleep(2)

            print("📤 Enviando Telegram...")
            subprocess.run(["python", "enviar_telegram.py"])

            print("✅ Ciclo completado")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("⏳ Esperando 1 hora...")
        time.sleep(3600)

# Ejecuta el bot en segundo plano
threading.Thread(target=iniciar_bot).start()

# Ruta web para Render
@app.route("/")
def home():
    return "✅ Bot de apuestas funcionando en Render"

# Servidor Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)