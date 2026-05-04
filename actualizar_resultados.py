import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"


def obtener_resultados_fecha(fecha):
    url = f"{BASE_URL}/fixtures"

    params = {
        "date": fecha
    }

    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json().get("response", [])

    resultados = []

    for p in data:
        # solo partidos terminados
        if p["fixture"]["status"]["short"] != "FT":
            continue

        local = p["teams"]["home"]["name"]
        visitante = p["teams"]["away"]["name"]

        partido = f"{local} vs {visitante}"

        goles_local = p["goals"]["home"]
        goles_visitante = p["goals"]["away"]

        resultados.append({
            "partido": partido,
            "goles_local": goles_local,
            "goles_visitante": goles_visitante
        })

    return resultados


def guardar_resultados(resultados):
    df_nuevo = pd.DataFrame(resultados)

    if os.path.exists("resultados.csv"):
        df_existente = pd.read_csv("resultados.csv")
        df_total = pd.concat([df_existente, df_nuevo])
        df_total = df_total.drop_duplicates(subset=["partido"])
    else:
        df_total = df_nuevo

    df_total.to_csv("resultados.csv", index=False)


if __name__ == "__main__":
    # 🔥 AUTOMÁTICO: toma AYER
    fecha = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"📅 Buscando resultados de: {fecha}")

    resultados = obtener_resultados_fecha(fecha)

    if resultados:
        guardar_resultados(resultados)
        print(f"✅ {len(resultados)} resultados guardados")
    else:
        print("⚠️ No hay resultados disponibles")