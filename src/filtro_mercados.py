import csv, os

ruta = os.path.join(os.path.dirname(__file__), "..", "picks.csv")

def mercados_rentables():
    if not os.path.exists(ruta):
        return []

    mercados = {}

    with open(ruta, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for p in reader:
            m = p["mercado"]

            if m not in mercados:
                mercados[m] = {"total":0,"wins":0}

            mercados[m]["total"] += 1

            if p["resultado"] == "win":
                mercados[m]["wins"] += 1

    buenos = []

    for m in mercados:
        t = mercados[m]["total"]
        w = mercados[m]["wins"]

        if t < 5:
            continue

        winrate = w / t

        if winrate >= 0.55:
            buenos.append(m)

    return buenos