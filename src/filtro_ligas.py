import csv, os

ruta = os.path.join(os.path.dirname(__file__), "..", "picks.csv")

def ligas_rentables():
    if not os.path.exists(ruta):
        return []

    ligas = {}

    with open(ruta, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for p in reader:
            liga = p["partido"]  # ⚠️ luego mejoramos esto

            if liga not in ligas:
                ligas[liga] = {"total":0,"profit":0}

            ligas[liga]["total"] += 1

            try:
                ligas[liga]["profit"] += float(p["profit"])
            except:
                pass

    buenas = []

    for l in ligas:
        t = ligas[l]["total"]
        profit = ligas[l]["profit"]

        if t < 5:
            continue

        if profit > 0:
            buenas.append(l)

    return buenas