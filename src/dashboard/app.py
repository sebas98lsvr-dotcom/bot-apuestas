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
    # ESTADISTICAS
    # =========================

    total = len(df)

    wins = len(
        df[df["resultado"] == "win"]
    ) if not df.empty else 0

    losses = len(
        df[df["resultado"] == "loss"]
    ) if not df.empty else 0

    pendientes = len(
        df[df["resultado"] == "pendiente"]
    ) if not df.empty else 0

    profit = (
        round(df["profit"].sum(), 2)
        if not df.empty
        else 0
    )

    stake_total = (
        round(df["stake"].sum(), 2)
        if not df.empty
        else 0
    )

    # =========================
    # WINRATE
    # =========================

    if (wins + losses) > 0:

        winrate = round(
            (wins / (wins + losses)) * 100,
            2
        )

    else:
        winrate = 0

    # =========================
    # ROI
    # =========================

    if stake_total > 0:

        roi = round(
            (profit / stake_total) * 100,
            2
        )

    else:
        roi = 0

    # =========================
    # HISTORIAL
    # =========================

    historial = []

    if not df.empty:

        historial = (
            df.sort_values(
                by="fecha",
                ascending=False
            )
            .to_dict(orient="records")
        )

    # =========================
    # MERCADOS
    # =========================

    mercados = []

    if not df.empty:

        for mercado in df["mercado"].unique():

            d = df[
                df["mercado"] == mercado
            ]

            total_m = len(d)

            w = len(
                d[d["resultado"] == "win"]
            )

            l = len(
                d[d["resultado"] == "loss"]
            )

            if (w + l) > 0:

                wr = round(
                    (w / (w + l)) * 100,
                    2
                )

            else:
                wr = 0

            profit_m = round(
                d["profit"].sum(),
                2
            )

            mercados.append({

                "mercado": mercado,
                "total": total_m,
                "winrate": wr,
                "profit": profit_m
            })

    # =========================
    # GRAFICA PROFIT
    # =========================

    profits = []

    if not df.empty:

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

    if not df.empty:

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

    # =========================
    # STATS
    # =========================

    stats = {

        "total": total,
        "wins": wins,
        "losses": losses,
        "pendientes": pendientes,
        "winrate": winrate,
        "roi": roi,
        "profit_total": profit,
        "stake_total": stake_total,
        "mercados": {}
    }

    for m in mercados:

        stats["mercados"][m["mercado"]] = {

            "total": m["total"],
            "winrate": m["winrate"],
            "profit": m["profit"]
        }

    return render_template(

        "index.html",

        stats=stats,
        historial=historial,
        mercados=mercados,
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