from flask import Flask, render_template
import csv
import os

app = Flask(__name__)

# =========================
# CARGAR PICKS
# =========================
def cargar_picks():

    ruta = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "picks.csv"
    )

    if not os.path.exists(ruta):
        return [], {}

    picks = []

    with open(ruta, newline="", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            try:

                row["profit"] = float(
                    row.get("profit", 0)
                )

                row["odd"] = float(
                    row.get("odd", 0)
                )

                row["value"] = float(
                    row.get("value", 0)
                )

                row["stake"] = float(
                    row.get("stake", 0)
                )

            except:
                continue

            picks.append(row)

    # Más recientes primero
    picks = picks[::-1]

    # =========================
    # STATS GENERALES
    # =========================
    total = len(picks)

    ganados = sum(
        1 for p in picks
        if p.get("resultado") == "ganada"
    )

    perdidos = sum(
        1 for p in picks
        if p.get("resultado") == "perdida"
    )

    pendientes = sum(
        1 for p in picks
        if p.get("resultado") == "pendiente"
    )

    profit_total = round(
        sum(p["profit"] for p in picks),
        2
    )

    stake_total = round(
        sum(p["stake"] for p in picks),
        2
    )

    winrate = round(
        (ganados / (ganados + perdidos)) * 100,
        2
    ) if (ganados + perdidos) else 0

    roi = round(
        (profit_total / stake_total) * 100,
        2
    ) if stake_total else 0

    # =========================
    # RENDIMIENTO POR MERCADO
    # =========================
    mercados = {}

    for p in picks:

        mercado = p.get("mercado", "Sin mercado")

        if mercado not in mercados:

            mercados[mercado] = {
                "total": 0,
                "wins": 0,
                "profit": 0
            }

        mercados[mercado]["total"] += 1

        mercados[mercado]["profit"] += p["profit"]

        if p.get("resultado") == "ganada":

            mercados[mercado]["wins"] += 1

    # Calcular winrate por mercado
    for mercado in mercados:

        total_m = mercados[mercado]["total"]

        wins_m = mercados[mercado]["wins"]

        mercados[mercado]["winrate"] = round(
            (wins_m / total_m) * 100,
            2
        ) if total_m else 0

    # =========================
    # STATS
    # =========================
    stats = {
        "total": total,
        "ganados": ganados,
        "perdidos": perdidos,
        "pendientes": pendientes,
        "profit_total": profit_total,
        "stake_total": stake_total,
        "winrate": winrate,
        "roi": roi,
        "mercados": mercados
    }

    return picks, stats

# =========================
# HOME
# =========================
@app.route("/")
def index():

    picks, stats = cargar_picks()

    return render_template(
        "index.html",
        picks=picks,
        stats=stats
    )

# =========================
# START
# =========================
if __name__ == "__main__":

    app.run(
        debug=True
    )