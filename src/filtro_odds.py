import csv, os

ruta = os.path.join(os.path.dirname(__file__), "..", "picks.csv")

def odds_rentables():
    if not os.path.exists(ruta):
        return (1.5, 3.0)

    rangos = {
        "bajo": {"total":0,"profit":0},
        "medio": {"total":0,"profit":0},
        "alto": {"total":0,"profit":0}
    }

    with open(ruta, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for p in reader:
            try:
                odd = float(p["odd"])
                profit = float(p["profit"])
            except:
                continue

            if odd < 1.7:
                r = "bajo"
            elif odd < 2.2:
                r = "medio"
            else:
                r = "alto"

            rangos[r]["total"] += 1
            rangos[r]["profit"] += profit

    mejor = None
    mejor_profit = -999

    for r in rangos:
        if rangos[r]["total"] < 5:
            continue

        if rangos[r]["profit"] > mejor_profit:
            mejor_profit = rangos[r]["profit"]
            mejor = r

    if mejor == "bajo":
        return (1.5, 1.7)
    elif mejor == "medio":
        return (1.7, 2.2)
    elif mejor == "alto":
        return (2.2, 4.0)

    return (1.5, 3.0)