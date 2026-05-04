import csv, os
from datetime import datetime
from api_datos import obtener_partidos, obtener_ultimos_partidos
from odds_api import obtener_odds
from modelo import *

BANK = 1000

def guardar(picks):
    ruta = os.path.join(os.path.dirname(__file__), "..", "picks.csv")

    crear = not os.path.exists(ruta)

    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)

        if crear:
            w.writerow(["fecha","fixture_id","partido","mercado","odd","prob","value","stake"])

        for p in picks:
            w.writerow([
                datetime.now(),
                p["fixture_id"],
                p["match"],
                p["market"],
                p["odd"],
                round(p["prob"],2),
                round(p["value"],2),
                round(p["stake"],2)
            ])

def main():
    partidos = obtener_partidos()
    picks = []

    for p in partidos:

        if p["fixture"]["status"]["short"] != "NS":
            continue

        fixture_id = p["fixture"]["id"]
        local = p["teams"]["home"]["name"]
        visitante = p["teams"]["away"]["name"]

        # 🔥 valores base simples (para no fallar)
        lamL, lamV = 1.4, 1.2

        prob_o = prob_over_25(lamL, lamV)
        prob_b = prob_btts(lamL, lamV)

        odds = obtener_odds(fixture_id)
        if not odds:
            continue

        try:
            bets = odds[0]["bookmakers"][0]["bets"]

            for b in bets:

                if b["name"] == "Goals Over/Under":
                    for v in b["values"]:
                        if v["value"] == "Over 2.5":
                            odd = float(v["odd"])
                            val = calcular_value(prob_o, odd)
                            stake = calcular_stake(BANK, val, odd)

                            if val > 0.05:   # 🔥 RELAJADO
                                picks.append({
                                    "fixture_id": fixture_id,
                                    "match": f"{local} vs {visitante}",
                                    "market": "Over 2.5",
                                    "odd": odd,
                                    "prob": prob_o,
                                    "value": val,
                                    "stake": stake
                                })

                if b["name"] == "Both Teams Score":
                    for v in b["values"]:
                        if v["value"] == "Yes":
                            odd = float(v["odd"])
                            val = calcular_value(prob_b, odd)
                            stake = calcular_stake(BANK, val, odd)

                            if val > 0.05:
                                picks.append({
                                    "fixture_id": fixture_id,
                                    "match": f"{local} vs {visitante}",
                                    "market": "BTTS",
                                    "odd": odd,
                                    "prob": prob_b,
                                    "value": val,
                                    "stake": stake
                                })

        except:
            continue

    print(f"\n🔥 Picks encontrados: {len(picks)}\n")
    guardar(picks)

if __name__ == "__main__":
    main()