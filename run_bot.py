import subprocess
import time

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

    # Espera 1 hora
    print("⏳ Esperando 1 hora...")
    time.sleep(3600)