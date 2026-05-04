import pandas as pd

# 🔥 detectar si hay header automáticamente
picks = pd.read_csv("picks.csv")

# si NO tiene columna 'partido', es porque no tiene header
if "partido" not in picks.columns:
    picks = pd.read_csv("picks.csv", header=None)
    picks.columns = ["fecha", "fixture_id", "partido", "mercado", "odd", "prob", "value"]

# leer resultados
resultados = pd.read_csv("resultados.csv")

# normalizar texto
picks["partido"] = picks["partido"].astype(str).str.strip().str.lower()
resultados["partido"] = resultados["partido"].astype(str).str.strip().str.lower()

bank = 1000
stake = 10

ganadas = 0
perdidas = 0

print("\n📊 BACKTEST\n")

for _, row in picks.iterrows():

    partido = row["partido"]

    # 🔥 ignorar si es header colado
    if partido == "partido":
        continue

    match = resultados[resultados["partido"] == partido]

    if match.empty:
        print(f"⚠️ No encontrado: {partido}")
        continue

    goles_local = match.iloc[0]["goles_local"]
    goles_visitante = match.iloc[0]["goles_visitante"]

    win = False

    if row["mercado"] == "Over 2.5":
        if goles_local + goles_visitante > 2:
            win = True

    if row["mercado"] == "BTTS":
        if goles_local > 0 and goles_visitante > 0:
            win = True

    if win:
        ganadas += 1
        bank += stake * (row["odd"] - 1)
    else:
        perdidas += 1
        bank -= stake

print("\n💰 RESULTADOS\n")
print("Bank final:", bank)
print("Ganadas:", ganadas)
print("Perdidas:", perdidas)
print("Total:", ganadas + perdidas)

roi = ((bank - 1000) / 1000) * 100
print(f"ROI: {roi:.2f}%")