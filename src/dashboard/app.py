import os
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

# =========================
# RUTA CSV
# =========================

ruta_csv = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "picks.csv"
)

# =========================
# HOME
# =========================

@app.route("/")
def home():

    try:

        df = pd.read_csv(ruta_csv)

    except:

        df = pd.DataFrame()

    # =========================
    # SI NO HAY PICKS
    # =========================

    if df.empty:

        stats = {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "pendientes": 0,
            "winrate": 0,
            "roi": 0,
            "profit": 0,
            "stake_total": 0
        }

        mercados = []

        historial = []

        profits = []

        winrates = []

    else:

        # =========================
        # ESTADISTICAS
        # =========================

        total = len(df)

        wins = len(
            df[df["resultado"] == "win"]
        )

        losses = len(
            df[df["resultado"] == "loss"]
        )

        pendientes = len(
            df[df["resultado"] == "pendiente"]
        )

        stake_total = df["stake"].sum()

        profit_total = df["profit"].sum()

        if wins + losses > 0:

            winrate = round(
                (wins / (wins + losses)) * 100,
                2
            )

        else:
            winrate = 0

        if stake_total > 0:

            roi = round(
                (profit_total / stake_total) * 100,
                2
            )

        else:
            roi = 0

        stats = {
            "total": total,
            "wins": wins,
            "losses": losses,
            "pendientes": pendientes,
            "winrate": winrate,
            "roi": roi,
            "profit": round(profit_total, 2),
            "stake_total": round(stake_total, 2)
        }

        # =========================
        # MERCADOS
        # =========================

        mercados = []

        for mercado in df["mercado"].unique():

            d = df[
                df["mercado"] == mercado
            ]

            w = len(
                d[d["resultado"] == "win"]
            )

            l = len(
                d[d["resultado"] == "loss"]
            )

            total_ml = w + l

            if total_ml > 0:

                wr = round(
                    (w / total_ml) * 100,
                    2
                )

            else:
                wr = 0

            profit = round(
                d["profit"].sum(),
                2
            )

            mercados.append({
                "mercado": mercado,
                "total": len(d),
                "winrate": wr,
                "profit": profit
            })

        # =========================
        # HISTORIAL
        # =========================

        historial = df.sort_values(
            by="fecha",
            ascending=False
        ).to_dict(orient="records")

        # =========================
        # GRAFICA PROFIT
        # =========================

        df["profit_acumulado"] = (
            df["profit"].cumsum()
        )

        profits = df[
            "profit_acumulado"
        ].tolist()

        # =========================
        # GRAFICA WINRATE
        # =========================

        winrates = []

        acumulado_w = 0
        acumulado_total = 0

        for _, row in df.iterrows():

            if row["resultado"] == "win":
                acumulado_w += 1

            if row["resultado"] != "pendiente":
                acumulado_total += 1

            if acumulado_total > 0:

                wr = (
                    acumulado_w
                    / acumulado_total
                ) * 100

            else:
                wr = 0

            winrates.append(
                round(wr, 2)
            )

    return render_template(
        "index.html",
        stats=stats,
        mercados=mercados,
        historial=historial,
        profits=profits,
        winrates=winrates
    )

# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000,
        debug=False
    )